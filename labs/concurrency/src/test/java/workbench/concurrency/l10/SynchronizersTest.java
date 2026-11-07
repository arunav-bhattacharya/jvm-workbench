package workbench.concurrency.l10;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class SynchronizersTest {

    private static Thread daemon(Runnable r) {
        Thread t = new Thread(r);
        t.setDaemon(true);
        t.start();
        return t;
    }

    private static boolean reachesWaiting(Thread t) throws InterruptedException {
        for (int i = 0; i < 500; i++) {
            Thread.State s = t.getState();
            if (s == Thread.State.WAITING || s == Thread.State.TIMED_WAITING) return true;
            Thread.sleep(10);
        }
        return false;
    }

    /** Takes every permit of the gate with tasks that block until {@code release} opens. */
    private static List<Thread> occupy(IssuerGate gate, int n, CountDownLatch release) throws InterruptedException {
        CountDownLatch inside = new CountDownLatch(n);
        List<Thread> holders = new ArrayList<>();
        for (int i = 0; i < n; i++) {
            holders.add(daemon(() -> {
                try {
                    gate.call(() -> { inside.countDown(); release.await(); return null; });
                } catch (Exception e) {
                    // the test's assertions report what matters
                }
            }));
        }
        assertThat(inside.await(5, java.util.concurrent.TimeUnit.SECONDS)).as("holders got their permits").isTrue();
        return holders;
    }

    // ---------- IssuerGate ----------

    @Test
    @DisplayName("IssuerGate: 32 callers, never more than 4 calls in flight, and 4 do run together")
    void neverMoreThanFour() throws Exception {
        IssuerGate gate = new IssuerGate(4);
        AtomicInteger inFlight = new AtomicInteger(), peak = new AtomicInteger();
        List<Thread> callers = new ArrayList<>();
        for (int i = 0; i < 32; i++) {
            callers.add(daemon(() -> {
                try {
                    gate.call(() -> {
                        peak.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                        Thread.sleep(30);
                        inFlight.decrementAndGet();
                        return "approved";
                    });
                } catch (Exception e) {
                    throw new IllegalStateException(e);
                }
            }));
        }
        for (Thread t : callers) t.join(15_000);
        assertThat(peak.get()).as("most calls in flight at once").isEqualTo(4);
        assertThat(gate.available()).isEqualTo(4);
    }

    @Test
    @DisplayName("IssuerGate: a task that throws still gives its permit back")
    void permitReturnedOnFailure() {
        IssuerGate gate = new IssuerGate(2);
        assertThatThrownBy(() -> gate.call(() -> { throw new IllegalStateException("issuer said 500"); }))
                .isInstanceOf(IllegalStateException.class);
        assertThat(gate.available()).isEqualTo(2);
    }

    @Test
    @DisplayName("IssuerGate: the timed call throws TimeoutException when all permits are busy, without running the task")
    void timedCallGivesUp() throws Exception {
        IssuerGate gate = new IssuerGate(2);
        CountDownLatch release = new CountDownLatch(1);
        List<Thread> holders = occupy(gate, 2, release);
        AtomicBoolean ran = new AtomicBoolean();
        assertTimeoutPreemptively(Duration.ofSeconds(5), () ->
                assertThatThrownBy(() -> gate.call(() -> { ran.set(true); return "approved"; }, Duration.ofMillis(100)))
                        .isInstanceOf(TimeoutException.class));
        assertThat(ran.get()).as("task ran without a permit").isFalse();
        release.countDown();
        for (Thread t : holders) t.join(5_000);
        assertThat(gate.available()).as("permits after everyone is done").isEqualTo(2);
    }

    @Test
    @DisplayName("IssuerGate: a caller interrupted while waiting for a permit does not add a permit")
    void interruptedWaiterAddsNothing() throws Exception {
        IssuerGate gate = new IssuerGate(2);
        CountDownLatch release = new CountDownLatch(1);
        List<Thread> holders = occupy(gate, 2, release);
        AtomicReference<Throwable> thrown = new AtomicReference<>();
        Thread waiter = daemon(() -> {
            try { gate.call(() -> "approved"); } catch (Throwable e) { thrown.set(e); }
        });
        assertThat(reachesWaiting(waiter)).isTrue();
        waiter.interrupt();
        waiter.join(5_000);
        assertThat(thrown.get()).isInstanceOf(InterruptedException.class);
        release.countDown();
        for (Thread t : holders) t.join(5_000);
        assertThat(gate.available()).as("permits after everyone is done").isEqualTo(2);
    }

    // ---------- RoundRunner ----------

    @Test
    @DisplayName("RoundRunner: 4 workers x 50 rounds; each round's total is the sum of its 4 shares, passed on once, in order")
    void roundTotals() {
        List<Long> totals = new CopyOnWriteArrayList<>();
        assertTimeoutPreemptively(Duration.ofSeconds(10),
                () -> RoundRunner.run(4, 50, (w, r) -> w * 1_000 + r, totals::add));
        List<Long> expected = new ArrayList<>();
        for (int r = 0; r < 50; r++) expected.add(6_000L + 4L * r);   // 0 + 1,000 + 2,000 + 3,000, plus 4 x r
        assertThat(totals).containsExactlyElementsOf(expected);
    }

    @Test
    @DisplayName("RoundRunner: workers run on 4 threads, and none starts round r+1 before round r's total is passed on")
    void roundsDontOverlap() {
        List<Long> totals = new CopyOnWriteArrayList<>();
        Set<String> threads = ConcurrentHashMap.newKeySet();
        AtomicInteger early = new AtomicInteger();
        assertTimeoutPreemptively(Duration.ofSeconds(10), () -> RoundRunner.run(4, 200, (w, r) -> {
            threads.add(Thread.currentThread().getName());
            if (totals.size() != r) early.incrementAndGet();      // round r may start only after r totals exist
            if (w == 0) Thread.onSpinWait();
            return 1;
        }, totals::add));
        assertThat(early.get()).as("steps that started before the previous round was totalled").isZero();
        assertThat(threads).as("worker threads").hasSize(4);
        assertThat(totals).hasSize(200).containsOnly(4L);
    }
}
