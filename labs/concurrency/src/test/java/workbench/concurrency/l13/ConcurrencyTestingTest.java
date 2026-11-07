package workbench.concurrency.l13;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

import static org.assertj.core.api.Assertions.assertThat;

@Timeout(30)   // a hung harness fails the test instead of hanging the build
class ConcurrencyTestingTest {

    // ---------- states used with Stress ----------

    // volatile keeps the JIT from batching the increments in a register; it does NOT make ++ atomic
    static final class VolatileCounter { volatile int count; }

    /** A refund ledger with the classic check-then-act race, written by the test, not by you. */
    static final class RacyLedger {
        final Map<String, Long> refunded = new ConcurrentHashMap<>();
        final AtomicLong approved = new AtomicLong();
        void refund(long cents) {
            long already = refunded.getOrDefault("pay-1", 0L);
            if (already + cents > 10_000) return;
            for (int i = 0; i < 100; i++) Thread.onSpinWait();
            refunded.put("pay-1", already + cents);
            approved.addAndGet(cents);
        }
        boolean ok() { return approved.get() <= 10_000 && refunded.getOrDefault("pay-1", 0L) == approved.get(); }
    }

    // ---------- Stress ----------

    @Test
    @DisplayName("Stress: setup once per round, threads x perThread actor calls, one invariant check per round")
    void stressCountsCalls() throws Exception {
        AtomicInteger setups = new AtomicInteger(), actors = new AtomicInteger(), checks = new AtomicInteger();
        int failed = Stress.failingRounds(5, 4, 10,
                setups::incrementAndGet,
                round -> actors.incrementAndGet(),
                round -> { checks.incrementAndGet(); return round % 2 == 1; });   // rounds 2 and 4 "fail"
        assertThat(setups.get()).as("setup calls").isEqualTo(5);
        assertThat(actors.get()).as("actor calls").isEqualTo(5 * 4 * 10);
        assertThat(checks.get()).as("invariant checks").isEqualTo(5);
        assertThat(failed).as("failing rounds").isEqualTo(2);
    }

    @Test
    @DisplayName("Stress: the threads of a round run at the same time")
    void stressThreadsOverlap() throws Exception {
        int failed = Stress.failingRounds(3, 6, 1,
                () -> new Object[] {new CyclicBarrier(6), new AtomicBoolean(true)},
                s -> {
                    try {
                        ((CyclicBarrier) s[0]).await(5, TimeUnit.SECONDS);   // only passes if all 6 are running together
                    } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                        ((AtomicBoolean) s[1]).set(false);
                    }
                },
                s -> ((AtomicBoolean) s[1]).get());
        assertThat(failed).as("rounds whose threads did not overlap").isZero();
    }

    @Test
    @DisplayName("Stress: finds the lost updates in a volatile int counter (volatile is not atomic)")
    void stressCatchesCounterRace() throws Exception {
        int failed = Stress.failingRounds(10, 8, 20_000, VolatileCounter::new, c -> c.count++, c -> c.count == 8 * 20_000);
        assertThat(failed).as("rounds that lost updates (out of 10)").isPositive();
    }

    @Test
    @DisplayName("Stress: reports no failures for an AtomicInteger counter")
    void stressPassesAtomicCounter() throws Exception {
        int failed = Stress.failingRounds(10, 8, 20_000, AtomicInteger::new, AtomicInteger::incrementAndGet, c -> c.get() == 8 * 20_000);
        assertThat(failed).isZero();
    }

    @Test
    @DisplayName("Stress: finds the over-refund race in a check-then-act ledger")
    void stressCatchesRefundRace() throws Exception {
        int failed = Stress.failingRounds(10, 8, 2_000, RacyLedger::new, l -> l.refund(1), RacyLedger::ok);
        assertThat(failed).as("rounds that refunded more than was captured or lost a refund").isPositive();
    }

    // ---------- RefundLedger ----------

    @Test
    @DisplayName("RefundLedger: refunds up to the captured amount, never beyond, and rejects unknown payments")
    void ledgerRules() {
        RefundLedger ledger = new RefundLedger(Map.of("pay-1", 1_000L));
        assertThat(ledger.refund("pay-1", 600)).isTrue();
        assertThat(ledger.refund("pay-1", 500)).isFalse();
        assertThat(ledger.refund("pay-1", 400)).isTrue();
        assertThat(ledger.refund("pay-1", 1)).isFalse();
        assertThat(ledger.refunded("pay-1")).isEqualTo(1_000);
        assertThat(ledger.refund("pay-404", 10)).isFalse();
        assertThat(ledger.refund("pay-1", 0)).isFalse();
    }

    @Test
    @DisplayName("RefundLedger: 8 threads x 2,000 one-cent refunds against 10,000 captured: exactly 10,000 refunded, 5 rounds")
    void ledgerUnderLoad() throws Exception {
        for (int round = 0; round < 5; round++) {
            RefundLedger ledger = new RefundLedger(Map.of("pay-1", 10_000L));
            AtomicLong approved = new AtomicLong();
            CountDownLatch go = new CountDownLatch(1);
            List<Thread> threads = new ArrayList<>();
            for (int t = 0; t < 8; t++) {
                Thread th = new Thread(() -> {
                    try { go.await(); } catch (InterruptedException e) { return; }
                    for (int i = 0; i < 2_000; i++) if (ledger.refund("pay-1", 1)) approved.incrementAndGet();
                });
                th.start();
                threads.add(th);
            }
            go.countDown();
            for (Thread th : threads) th.join();
            assertThat(approved.get()).as("refunds approved in round %d", round).isEqualTo(10_000);
            assertThat(ledger.refunded("pay-1")).as("refunded total in round %d", round).isEqualTo(10_000);
        }
    }
}
