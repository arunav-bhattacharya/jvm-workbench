package workbench.executors.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class TinyPoolTest {

    private static void await(CountDownLatch latch) {
        try {
            latch.await();
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    @Test
    @DisplayName("runs every task exactly once")
    void runsEveryTask() throws Exception {
        TinyPool pool = new TinyPool(4, "pay-");
        AtomicInteger runs = new AtomicInteger();
        for (int i = 0; i < 1_000; i++) pool.execute(runs::incrementAndGet);
        pool.shutdown();
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).as("terminated in time").isTrue();
        assertThat(runs.get()).isEqualTo(1_000);
    }

    @Test
    @DisplayName("runs tasks on its own N named threads, reused across tasks")
    void reusesItsThreads() throws Exception {
        TinyPool pool = new TinyPool(3, "pay-");
        Set<String> names = ConcurrentHashMap.newKeySet();
        for (int i = 0; i < 200; i++) pool.execute(() -> names.add(Thread.currentThread().getName()));
        pool.shutdown();
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).isTrue();
        assertThat(names).isNotEmpty().isSubsetOf("pay-0", "pay-1", "pay-2");
    }

    @Test
    @DisplayName("runs N tasks at the same time, and never more than N")
    void runsNAtOnce() throws Exception {
        int n = 3;
        TinyPool pool = new TinyPool(n, "pay-");
        // phase 1: n tasks meet at a barrier, which only works if all n run at the same moment
        CyclicBarrier allHere = new CyclicBarrier(n);
        AtomicInteger met = new AtomicInteger();
        for (int i = 0; i < n; i++) {
            pool.execute(() -> {
                try {
                    allHere.await(5, TimeUnit.SECONDS);
                    met.incrementAndGet();
                } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                    // leaves met short
                }
            });
        }
        // phase 2: 30 short tasks; count how many are inside at once
        AtomicInteger inside = new AtomicInteger();
        AtomicInteger maxInside = new AtomicInteger();
        for (int i = 0; i < 30; i++) {
            pool.execute(() -> {
                int now = inside.incrementAndGet();
                maxInside.accumulateAndGet(now, Math::max);
                try { Thread.sleep(5); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                inside.decrementAndGet();
            });
        }
        pool.shutdown();
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).isTrue();
        assertThat(met.get()).as("tasks that ran together").isEqualTo(n);
        assertThat(maxInside.get()).as("most tasks running at once").isLessThanOrEqualTo(n);
    }

    @Test
    @DisplayName("shutdown returns at once, and the queued tasks still run")
    void shutdownDoesNotWait() throws Exception {
        TinyPool pool = new TinyPool(1, "pay-");
        CountDownLatch release = new CountDownLatch(1);
        AtomicInteger runs = new AtomicInteger();
        pool.execute(() -> { await(release); runs.incrementAndGet(); });
        pool.execute(runs::incrementAndGet);
        pool.execute(runs::incrementAndGet);

        pool.shutdown();                       // the first task is still blocked
        assertThat(pool.isShutdown()).isTrue();
        assertThat(pool.isTerminated()).as("terminated while a task is blocked?").isFalse();
        assertThat(pool.awaitTermination(50, TimeUnit.MILLISECONDS)).as("awaitTermination while blocked").isFalse();

        release.countDown();
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).isTrue();
        assertThat(runs.get()).as("tasks that ran").isEqualTo(3);
        assertThat(pool.isTerminated()).isTrue();
    }

    @Test
    @DisplayName("execute after shutdown throws RejectedExecutionException")
    void rejectsAfterShutdown() throws Exception {
        TinyPool pool = new TinyPool(2, "pay-");
        pool.shutdown();
        assertThatThrownBy(() -> pool.execute(() -> { })).isInstanceOf(RejectedExecutionException.class);
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).isTrue();
    }

    @Test
    @DisplayName("shutdownNow interrupts the running task and returns the ones that never started")
    void shutdownNowHandsBackTheRest() throws Exception {
        TinyPool pool = new TinyPool(1, "pay-");
        CountDownLatch started = new CountDownLatch(1);
        AtomicBoolean sawInterrupt = new AtomicBoolean();
        pool.execute(() -> {
            started.countDown();
            try {
                Thread.sleep(30_000);          // a slow call that respects interrupts
            } catch (InterruptedException e) {
                sawInterrupt.set(true);
            }
        });
        AtomicInteger laterRuns = new AtomicInteger();
        List<Runnable> queued = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            Runnable r = laterRuns::incrementAndGet;
            queued.add(r);
            pool.execute(r);
        }
        assertThat(started.await(5, TimeUnit.SECONDS)).isTrue();

        List<Runnable> neverStarted = pool.shutdownNow();

        assertThat(neverStarted).containsExactlyElementsOf(queued);
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).as("terminated after shutdownNow").isTrue();
        assertThat(sawInterrupt.get()).as("running task was interrupted").isTrue();
        assertThat(laterRuns.get()).as("queued tasks that ran anyway").isZero();
    }

    @Test
    @DisplayName("a task that throws does not kill its worker")
    void survivesFailingTasks() throws Exception {
        TinyPool pool = new TinyPool(1, "solo-");
        for (int i = 0; i < 5; i++) pool.execute(() -> { throw new IllegalStateException("card issuer said no"); });
        AtomicInteger ranAfter = new AtomicInteger();
        Set<String> names = ConcurrentHashMap.newKeySet();
        pool.execute(() -> { ranAfter.incrementAndGet(); names.add(Thread.currentThread().getName()); });
        pool.shutdown();
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).isTrue();
        assertThat(ranAfter.get()).as("task after the failures ran").isEqualTo(1);
        assertThat(names).containsExactly("solo-0");
        assertThat(pool.failedTasks()).isEqualTo(5);
    }

    @Test
    @DisplayName("close() in try-with-resources waits for every queued task")
    void closeWaits() {
        AtomicInteger runs = new AtomicInteger();
        try (TinyPool pool = new TinyPool(2, "pay-")) {
            for (int i = 0; i < 50; i++) {
                pool.execute(() -> {
                    try { Thread.sleep(2); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                    runs.incrementAndGet();
                });
            }
        }
        assertThat(runs.get()).isEqualTo(50);
    }
}
