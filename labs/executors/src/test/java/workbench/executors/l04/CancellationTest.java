package workbench.executors.l04;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.FutureTask;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CancellationTest {
    // daemon threads, so a poller that refuses to stop can't keep the test JVM alive
    private final ExecutorService pool = Executors.newFixedThreadPool(2, r -> {
        Thread t = new Thread(r, "test-worker");
        t.setDaemon(true);
        return t;
    });

    @AfterEach
    void stopPool() {
        pool.shutdownNow();
    }

    @Test
    @DisplayName("getOrDefault returns the result when the task finishes in time")
    void returnsResult() throws Exception {
        Future<Integer> f = pool.submit(() -> 42);
        assertThat(Futures.getOrDefault(f, Duration.ofSeconds(5), -1)).isEqualTo(42);
    }

    @Test
    @DisplayName("getOrDefault on timeout returns the fallback and interrupts the task")
    void timeoutCancelsAndInterrupts() throws Exception {
        CountDownLatch sawInterrupt = new CountDownLatch(1);
        Future<Integer> slow = pool.submit(() -> {
            try {
                Thread.sleep(30_000);                 // an issuer that never answers
                return 1;
            } catch (InterruptedException e) {
                sawInterrupt.countDown();
                throw e;
            }
        });
        assertThat(Futures.getOrDefault(slow, Duration.ofMillis(100), -1)).isEqualTo(-1);
        assertThat(slow.isCancelled()).as("future cancelled").isTrue();
        assertThat(sawInterrupt.await(5, TimeUnit.SECONDS)).as("task was interrupted").isTrue();
    }

    @Test
    @DisplayName("getOrDefault returns the fallback when the task fails")
    void failureFallsBack() throws Exception {
        Future<Integer> f = pool.submit(() -> { throw new IllegalStateException("issuer said 503"); });
        assertThat(Futures.getOrDefault(f, Duration.ofSeconds(5), -1)).isEqualTo(-1);
    }

    @Test
    @DisplayName("getOrDefault cancels the task and rethrows when the caller is interrupted")
    void callerInterrupted() throws Exception {
        CountDownLatch never = new CountDownLatch(1);
        Future<Integer> f = pool.submit(() -> { never.await(); return 1; });
        Thread.currentThread().interrupt();
        try {
            assertThatThrownBy(() -> Futures.getOrDefault(f, Duration.ofSeconds(5), -1))
                    .isInstanceOf(InterruptedException.class);
            assertThat(f.isCancelled()).as("future cancelled").isTrue();
        } finally {
            Thread.interrupted();                     // clear the flag for the next test
        }
    }

    @Test
    @DisplayName("describe reports each Future.State without blocking")
    void describesStates() {
        FutureTask<Integer> running = new FutureTask<>(() -> 7);          // never run
        FutureTask<Integer> ok = new FutureTask<>(() -> 42);
        ok.run();
        FutureTask<Integer> failed = new FutureTask<>(() -> { throw new IllegalStateException("card declined"); });
        failed.run();
        FutureTask<Integer> cancelled = new FutureTask<>(() -> 1);
        cancelled.cancel(false);

        assertThat(Futures.describe(running)).isEqualTo("running");
        assertThat(Futures.describe(ok)).isEqualTo("success: 42");
        assertThat(Futures.describe(failed)).isEqualTo("failed: card declined");
        assertThat(Futures.describe(cancelled)).isEqualTo("cancelled");
    }

    /** Waits until the poller's thread is asleep, so the interrupt lands inside sleep(). */
    private static void awaitSleeping(AtomicReference<Thread> worker) throws InterruptedException {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        while (System.nanoTime() < deadline) {
            Thread t = worker.get();
            if (t != null && t.getState() == Thread.State.TIMED_WAITING) return;
            Thread.sleep(1);
        }
        throw new AssertionError("poller never went to sleep");
    }

    @Test
    @DisplayName("StatementPoller stops when its executor calls shutdownNow")
    void pollerStopsOnShutdownNow() throws Exception {
        AtomicReference<Thread> worker = new AtomicReference<>();
        StatementPoller poller = new StatementPoller(() -> worker.set(Thread.currentThread()), Duration.ofMillis(50));
        ExecutorService own = Executors.newSingleThreadExecutor(r -> {
            Thread t = new Thread(r, "poller");
            t.setDaemon(true);
            return t;
        });
        own.execute(poller);
        awaitSleeping(worker);
        own.shutdownNow();
        assertThat(own.awaitTermination(5, TimeUnit.SECONDS)).as("poller stopped after shutdownNow").isTrue();
        assertThat(poller.polls()).isPositive();
    }

    @Test
    @DisplayName("StatementPoller stops when its Future is cancelled with cancel(true)")
    void pollerStopsOnCancel() throws Exception {
        AtomicReference<Thread> worker = new AtomicReference<>();
        StatementPoller poller = new StatementPoller(() -> worker.set(Thread.currentThread()), Duration.ofMillis(50));
        Future<?> f = pool.submit(poller);
        awaitSleeping(worker);
        f.cancel(true);
        // after cancel, the worker must leave run(): its state becomes WAITING (idle in the pool)
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5);
        int before;
        do {
            before = poller.polls();
            Thread.sleep(200);
        } while (poller.polls() != before && System.nanoTime() < deadline);
        assertThat(poller.polls()).as("polls keep growing after cancel(true)").isEqualTo(before);
    }
}
