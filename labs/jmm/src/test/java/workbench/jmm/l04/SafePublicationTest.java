package workbench.jmm.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.lang.reflect.Field;
import java.lang.reflect.Modifier;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SafePublicationTest {
    private static final long LET_THE_JIT_COMPILE_MS = 300;
    private static final long GENEROUS_JOIN_MS = 5_000;

    @Test
    @DisplayName("RateCard keeps its own copy: changing the caller's map later doesn't change the card")
    void defensiveCopy() {
        Map<String, Long> fees = new HashMap<>(Map.of("VISA", 120L, "MC", 135L));
        RateCard card = new RateCard("EUR", fees);
        fees.put("VISA", 999L);
        fees.put("AMEX", 300L);
        assertThat(card.feeFor("VISA")).isEqualTo(120L);
        assertThat(card.feesByScheme()).containsOnlyKeys("VISA", "MC");
    }

    @Test
    @DisplayName("RateCard's map can't be changed through its getter")
    void unmodifiableView() {
        RateCard card = new RateCard("EUR", new HashMap<>(Map.of("VISA", 120L)));
        assertThatThrownBy(() -> card.feesByScheme().put("VISA", 0L))
                .isInstanceOf(UnsupportedOperationException.class);
    }

    @Test
    @DisplayName("RateCard is a final class whose fields are all final, so it survives publication through a race")
    void finalFields() {
        assertThat(Modifier.isFinal(RateCard.class.getModifiers())).as("RateCard is final").isTrue();
        for (Field f : RateCard.class.getDeclaredFields()) {
            if (Modifier.isStatic(f.getModifiers())) continue;
            assertThat(Modifier.isFinal(f.getModifiers())).as("field %s is final", f.getName()).isTrue();
        }
    }

    @Test
    @DisplayName("RateCardRegistry: a reader already waiting in awaitFirst() sees the card the loader publishes")
    void waitingReaderSeesCard() throws InterruptedException {
        RateCardRegistry registry = new RateCardRegistry();
        AtomicReference<RateCard> seen = new AtomicReference<>();
        Thread reader = new Thread(() -> seen.set(registry.awaitFirst()), "request");
        reader.setDaemon(true);   // a stuck reader must not keep the test JVM alive
        reader.start();
        Thread.sleep(LET_THE_JIT_COMPILE_MS);

        RateCard card = new RateCard("EUR", Map.of("VISA", 120L));
        registry.publish(card);
        reader.join(GENEROUS_JOIN_MS);

        assertThat(reader.isAlive()).as("the request thread never saw the published card").isFalse();
        assertThat(seen.get()).isSameAs(card);
    }

    @Test
    @DisplayName("FraudMonitor: creating it while the bus replays an event under the limit works and flags nothing")
    void replayUnderLimit() {
        EventBus bus = new EventBus();
        bus.publish(new PaymentEvent("pay-1", 50_000));
        AtomicReference<FraudMonitor> monitor = new AtomicReference<>();
        assertThatCode(() -> monitor.set(FraudMonitor.create(bus, 100_000)))
                .as("the replayed event reached a half-built monitor")
                .doesNotThrowAnyException();
        assertThat(monitor.get().flagged()).isEmpty();
    }

    @Test
    @DisplayName("FraudMonitor: the replayed event and later events are judged against the real limit")
    void replayOverLimit() {
        EventBus bus = new EventBus();
        bus.publish(new PaymentEvent("pay-1", 150_000));
        FraudMonitor monitor = FraudMonitor.create(bus, 100_000);
        bus.publish(new PaymentEvent("pay-2", 20_000));
        bus.publish(new PaymentEvent("pay-3", 100_001));
        assertThat(monitor.flagged()).containsExactly("pay-1", "pay-3");
    }
}
