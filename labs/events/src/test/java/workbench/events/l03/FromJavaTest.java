package workbench.events.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicLong;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatIllegalArgumentException;

/** The library as a Java team uses it. Everything here must compile and read like ordinary Java. */
class FromJavaTest {

    @Test
    @DisplayName("Java builds events through the facade, and the value classes still validate")
    void facadeValidates() {
        ParcelCollected c = Events.collected("PP-7781", 2_500);
        assertThat(Events.parcelId(c)).isEqualTo("PP-7781");
        assertThat(Events.grams(c)).isEqualTo(2_500L);
        assertThat(c).isEqualTo(Events.collected("PP-7781", 2_500));
        assertThatIllegalArgumentException().isThrownBy(() -> Events.collected("7781", 2_500)).withMessageContaining("7781");
        assertThatIllegalArgumentException().isThrownBy(() -> Events.collected("PP-7781", -1));
        assertThatIllegalArgumentException().isThrownBy(() -> Events.delivered("PP-7781", 0));
    }

    @Test
    @DisplayName("Java subscribes with a Class token, and a Handler<ParcelEvent> fits any subscription")
    void classTokensAndVariance() {
        EventBus bus = new EventBus();                                 // @JvmOverloads (and all defaults)
        List<String> seen = new CopyOnWriteArrayList<>();
        Handler<ParcelEvent> tracking = e -> seen.add("tracking " + Events.parcelId(e));
        bus.subscribe(ParcelCollected.class, c -> seen.add("load " + Events.grams(c)));
        bus.subscribe(ParcelCollected.class, tracking);                // Handler<? super E>
        bus.publish(Events.collected("PP-7781", 2_500));
        bus.publish(Events.delivered("PP-7781", 2_500));
        assertThat(seen).containsExactly("load 2500", "tracking PP-7781");
    }

    @Test
    @DisplayName("Java passes middleware and an error handler to the constructor it needs")
    void constructorOverloads() {
        EventBus deduping = new EventBus(List.of(new DropDuplicates()));   // exists because of @JvmOverloads
        List<Exception> errors = new ArrayList<>();
        EventBus reporting = new EventBus(List.of(), (event, error) -> errors.add(error));
        List<String> seen = new ArrayList<>();
        deduping.subscribe(ParcelEvent.class, e -> seen.add(e.toString()));
        deduping.publish(Events.collected("PP-7781", 2_500));
        deduping.publish(Events.collected("PP-7781", 2_500));          // the same scan, sent twice
        assertThat(seen).hasSize(1);
        reporting.subscribe(ParcelEvent.class, e -> { throw new IllegalStateException("load board is down"); });
        assertThat(reporting.publish(Events.collected("PP-7781", 2_500))).isEqualTo(1);
        assertThat(errors).hasSize(1);
        assertThat(errors.get(0)).hasMessage("load board is down");
    }

    @Test
    @DisplayName("Java uses the subscription DSL through a Consumer, and one handle closes it all")
    void dslFromJava() {
        EventBus bus = new EventBus();
        List<String> seen = new ArrayList<>();
        try (Subscription handle = Events.subscriptions(bus, b -> {
            b.on(ParcelCollected.class, c -> seen.add("load " + Events.grams(c)));
            b.on(Handover.class, h -> seen.add("handover " + Events.grams(h)));
        })) {
            bus.publish(Events.collected("PP-7781", 2_500));
            assertThat(bus.handlerCount()).isEqualTo(2);
        }                                                              // no catch: close() throws nothing
        assertThat(bus.handlerCount()).isZero();
        assertThat(seen).containsExactly("load 2500", "handover 2500");
    }

    @Test
    @DisplayName("Java times a handler with Handlers.timed and a fake Ticker")
    void timingFromJava() {
        AtomicLong clock = new AtomicLong();
        Timings timings = new Timings(() -> clock.addAndGet(250));
        EventBus bus = new EventBus();
        bus.subscribe(ParcelCollected.class, Handlers.timed(c -> { }, "load", timings));
        bus.publish(Events.collected("PP-7781", 2_500));
        assertThat(timings.calls("load")).isEqualTo(1);
        assertThat(timings.totalNanos("load")).isEqualTo(250L);
        assertThat(Ticker.SYSTEM).isNotNull();                          // @JvmField: no Companion.getSYSTEM()
    }

    // javac checks this switch for exhaustiveness: kotlinc wrote PermittedSubclasses for the Kotlin model
    private static String kind(ParcelEvent e) {
        return switch (e) {
            case ParcelBooked b -> "booked " + Events.grams(b);
            case DeliveryFailed f -> "failed " + f.getReason();
            case ParcelCollected c -> "collected " + Events.grams(c);
            case ParcelDelivered d -> "delivered " + Events.grams(d);
        };
    }

    @Test
    @DisplayName("Java switches exhaustively over the Kotlin sealed model")
    void exhaustiveSwitchFromJava() {
        assertThat(kind(Events.booked("PP-7781", 2_500))).isEqualTo("booked 2500");
        assertThat(kind(Events.failed("PP-7782", FailReason.NOBODY_HOME))).isEqualTo("failed NOBODY_HOME");
        assertThat(kind(Events.delivered("PP-7781", 2_500))).isEqualTo("delivered 2500");
    }

    @Test
    @DisplayName("SupportDesk counts failed attempts per parcel, adds up delivered weight, and stops after close")
    void supportDesk() {
        EventBus bus = new EventBus();
        SupportDesk desk = new SupportDesk(bus);
        bus.publish(Events.failed("PP-7781", FailReason.NOBODY_HOME));
        bus.publish(Events.failed("PP-7781", FailReason.NOBODY_HOME));
        bus.publish(Events.failed("PP-9001", FailReason.ADDRESS_NOT_FOUND));
        bus.publish(Events.collected("PP-7781", 2_500));
        bus.publish(Events.delivered("PP-7781", 2_500));
        bus.publish(Events.delivered("PP-9001", 500));
        assertThat(desk.failedAttempts("PP-7781")).isEqualTo(2);
        assertThat(desk.failedAttempts("PP-9001")).isEqualTo(1);
        assertThat(desk.failedAttempts("PP-0000")).isZero();
        assertThat(desk.deliveredGrams()).isEqualTo(3_000L);
        desk.close();
        assertThat(bus.handlerCount()).isZero();
        bus.publish(Events.failed("PP-7781", FailReason.NOBODY_HOME));
        bus.publish(Events.delivered("PP-7781", 2_500));
        assertThat(desk.failedAttempts("PP-7781")).isEqualTo(2);
        assertThat(desk.deliveredGrams()).isEqualTo(3_000L);
    }
}
