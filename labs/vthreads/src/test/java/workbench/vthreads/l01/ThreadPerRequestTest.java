package workbench.vthreads.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.within;

class ThreadPerRequestTest {

    /** A fake blocking handler: it sleeps like a call to a card issuer and counts how many run at once. */
    static final class FakeIssuerCall implements Runnable {
        final Duration latency;
        final AtomicInteger inFlight = new AtomicInteger();
        final AtomicInteger peak = new AtomicInteger();
        final AtomicInteger finished = new AtomicInteger();
        final Set<Thread> threads = ConcurrentHashMap.newKeySet();
        final AtomicInteger onVirtual = new AtomicInteger();

        FakeIssuerCall(Duration latency) { this.latency = latency; }

        @Override public void run() {
            Thread me = Thread.currentThread();
            threads.add(me);
            if (me.isVirtual()) onVirtual.incrementAndGet();
            peak.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
            try {
                Thread.sleep(latency);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            } finally {
                inFlight.decrementAndGet();
            }
            finished.incrementAndGet();
        }
    }

    @Test
    @DisplayName("Little's law: 1,500 authorizations/s at 200 ms each means 300 in flight")
    void inFlight() {
        assertThat(LittlesLaw.inFlight(1_500, Duration.ofMillis(200))).isCloseTo(300.0, within(1e-9));
        assertThat(LittlesLaw.inFlight(40, Duration.ofSeconds(3))).isCloseTo(120.0, within(1e-9));
    }

    @Test
    @DisplayName("Little's law: 200 threads at 200 ms each cap you at 1,000 requests/s")
    void maxThroughput() {
        assertThat(LittlesLaw.maxThroughput(200, Duration.ofMillis(200))).isCloseTo(1_000.0, within(1e-9));
        assertThat(LittlesLaw.maxThroughput(200, Duration.ofMillis(1_200))).isCloseTo(166.666_666, within(1e-3));
    }

    @Test
    @DisplayName("Fixed pool runs every task, never more than poolSize at once, and waits for all of them")
    void fixedPoolCapsConcurrency() {
        FakeIssuerCall call = new FakeIssuerCall(Duration.ofMillis(20));
        int completed = BlockingRunner.runOnFixedPool(8, 200, call);
        assertThat(completed).as("tasks reported as completed").isEqualTo(200);
        assertThat(call.finished.get()).as("tasks that had finished when the method returned").isEqualTo(200);
        assertThat(call.peak.get()).as("most tasks running at once").isBetween(2, 8);
        assertThat(call.threads).as("distinct threads used").hasSizeLessThanOrEqualTo(8);
        assertThat(call.onVirtual.get()).as("tasks that ran on a virtual thread").isZero();
    }

    @Test
    @DisplayName("Virtual threads run every task on its own new virtual thread and wait for all of them")
    void oneVirtualThreadPerTask() {
        FakeIssuerCall call = new FakeIssuerCall(Duration.ofMillis(20));
        int completed = BlockingRunner.runOnVirtualThreads(500, call);
        assertThat(completed).isEqualTo(500);
        assertThat(call.finished.get()).as("tasks that had finished when the method returned").isEqualTo(500);
        assertThat(call.onVirtual.get()).as("tasks that ran on a virtual thread").isEqualTo(500);
        assertThat(call.threads).as("distinct threads: one per task, no reuse").hasSize(500);
    }

    @Test
    @DisplayName("2,000 sleeping tasks: virtual threads finish far faster than a 100-thread pool")
    void virtualThreadsBeatTheWall() {
        Duration latency = Duration.ofMillis(100);

        FakeIssuerCall pooled = new FakeIssuerCall(latency);
        long t0 = System.nanoTime();
        assertThat(BlockingRunner.runOnFixedPool(100, 2_000, pooled)).isEqualTo(2_000);
        long poolMillis = (System.nanoTime() - t0) / 1_000_000;

        FakeIssuerCall virtual = new FakeIssuerCall(latency);
        long t1 = System.nanoTime();
        assertThat(BlockingRunner.runOnVirtualThreads(2_000, virtual)).isEqualTo(2_000);
        long virtualMillis = (System.nanoTime() - t1) / 1_000_000;

        // 2,000 tasks / 100 threads = 20 rounds of 100 ms, so the pool can never beat 2 s
        assertThat(poolMillis).as("pool time (ms)").isGreaterThanOrEqualTo(2_000);
        assertThat(pooled.peak.get()).as("pool: most tasks running at once").isLessThanOrEqualTo(100);
        // all 2,000 sleep at the same time; the margin is wide so a busy machine can't fail it
        assertThat(virtual.peak.get()).as("virtual: most tasks running at once").isGreaterThan(500);
        assertThat(virtualMillis).as("virtual time (ms) vs pool time " + poolMillis + " ms").isLessThan(poolMillis / 2);
    }
}
