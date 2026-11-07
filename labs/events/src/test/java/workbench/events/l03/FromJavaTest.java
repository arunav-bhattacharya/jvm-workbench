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
        PaymentCaptured c = Events.captured("pay_7781", 1_999);
        assertThat(Events.paymentId(c)).isEqualTo("pay_7781");
        assertThat(Events.amountMinor(c)).isEqualTo(1_999L);
        assertThat(c).isEqualTo(Events.captured("pay_7781", 1_999));
        assertThatIllegalArgumentException().isThrownBy(() -> Events.captured("7781", 1_999)).withMessageContaining("7781");
        assertThatIllegalArgumentException().isThrownBy(() -> Events.captured("pay_7781", -1));
        assertThatIllegalArgumentException().isThrownBy(() -> Events.refunded("pay_7781", 0));
    }

    @Test
    @DisplayName("Java subscribes with a Class token, and a Handler<PaymentEvent> fits any subscription")
    void classTokensAndVariance() {
        EventBus bus = new EventBus();                                 // @JvmOverloads (and all defaults)
        List<String> seen = new CopyOnWriteArrayList<>();
        Handler<PaymentEvent> audit = e -> seen.add("audit " + Events.paymentId(e));
        bus.subscribe(PaymentCaptured.class, c -> seen.add("ledger " + Events.amountMinor(c)));
        bus.subscribe(PaymentCaptured.class, audit);                   // Handler<? super E>
        bus.publish(Events.captured("pay_7781", 1_999));
        bus.publish(Events.refunded("pay_7781", 500));
        assertThat(seen).containsExactly("ledger 1999", "audit pay_7781");
    }

    @Test
    @DisplayName("Java passes middleware and an error handler to the constructor it needs")
    void constructorOverloads() {
        EventBus deduping = new EventBus(List.of(new DropDuplicates()));   // exists because of @JvmOverloads
        List<Exception> errors = new ArrayList<>();
        EventBus reporting = new EventBus(List.of(), (event, error) -> errors.add(error));
        List<String> seen = new ArrayList<>();
        deduping.subscribe(PaymentEvent.class, e -> seen.add(e.toString()));
        deduping.publish(Events.captured("pay_7781", 1_999));
        deduping.publish(Events.captured("pay_7781", 1_999));          // a redelivery
        assertThat(seen).hasSize(1);
        reporting.subscribe(PaymentEvent.class, e -> { throw new IllegalStateException("ledger is down"); });
        assertThat(reporting.publish(Events.captured("pay_7781", 1_999))).isEqualTo(1);
        assertThat(errors).hasSize(1);
        assertThat(errors.get(0)).hasMessage("ledger is down");
    }

    @Test
    @DisplayName("Java uses the subscription DSL through a Consumer, and one handle closes it all")
    void dslFromJava() {
        EventBus bus = new EventBus();
        List<String> seen = new ArrayList<>();
        try (Subscription handle = Events.subscriptions(bus, b -> {
            b.on(PaymentCaptured.class, c -> seen.add("credit " + Events.amountMinor(c)));
            b.on(MoneyMovement.class, m -> seen.add("moved " + Events.amountMinor(m)));
        })) {
            bus.publish(Events.captured("pay_7781", 1_999));
            assertThat(bus.handlerCount()).isEqualTo(2);
        }                                                              // no catch: close() throws nothing
        assertThat(bus.handlerCount()).isZero();
        assertThat(seen).containsExactly("credit 1999", "moved 1999");
    }

    @Test
    @DisplayName("Java times a handler with Handlers.timed and a fake Ticker")
    void timingFromJava() {
        AtomicLong clock = new AtomicLong();
        Timings timings = new Timings(() -> clock.addAndGet(250));
        EventBus bus = new EventBus();
        bus.subscribe(PaymentCaptured.class, Handlers.timed(c -> { }, "ledger", timings));
        bus.publish(Events.captured("pay_7781", 1_999));
        assertThat(timings.calls("ledger")).isEqualTo(1);
        assertThat(timings.totalNanos("ledger")).isEqualTo(250L);
        assertThat(Ticker.SYSTEM).isNotNull();                          // @JvmField: no Companion.getSYSTEM()
    }

    // javac checks this switch for exhaustiveness: kotlinc wrote PermittedSubclasses for the Kotlin model
    private static String kind(PaymentEvent e) {
        return switch (e) {
            case PaymentAuthorized a -> "authorized " + Events.amountMinor(a);
            case PaymentDeclined d -> "declined " + d.getReason();
            case PaymentCaptured c -> "captured " + Events.amountMinor(c);
            case PaymentRefunded r -> "refunded " + Events.amountMinor(r);
        };
    }

    @Test
    @DisplayName("Java switches exhaustively over the Kotlin sealed model")
    void exhaustiveSwitchFromJava() {
        assertThat(kind(Events.authorized("pay_7781", 1_999))).isEqualTo("authorized 1999");
        assertThat(kind(Events.declined("pay_7782", DeclineReason.CARD_EXPIRED))).isEqualTo("declined CARD_EXPIRED");
        assertThat(kind(Events.refunded("pay_7781", 500))).isEqualTo("refunded 500");
    }

    @Test
    @DisplayName("RefundDesk adds up refunds per payment, counts declines, and stops after close")
    void refundDesk() {
        EventBus bus = new EventBus();
        RefundDesk desk = new RefundDesk(bus);
        bus.publish(Events.refunded("pay_7781", 500));
        bus.publish(Events.refunded("pay_7781", 250));
        bus.publish(Events.refunded("pay_9001", 100));
        bus.publish(Events.captured("pay_7781", 1_999));
        bus.publish(Events.declined("pay_7782", DeclineReason.SUSPECTED_FRAUD));
        assertThat(desk.refundedMinor("pay_7781")).isEqualTo(750L);
        assertThat(desk.refundedMinor("pay_9001")).isEqualTo(100L);
        assertThat(desk.refundedMinor("pay_0000")).isZero();
        assertThat(desk.declines()).isEqualTo(1);
        desk.close();
        assertThat(bus.handlerCount()).isZero();
        bus.publish(Events.refunded("pay_7781", 500));
        assertThat(desk.refundedMinor("pay_7781")).isEqualTo(750L);
    }
}
