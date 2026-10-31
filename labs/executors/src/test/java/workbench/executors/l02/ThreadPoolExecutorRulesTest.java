package workbench.executors.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.SynchronousQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ThreadPoolExecutorRulesTest {
    static final int UNBOUNDED = Integer.MAX_VALUE;

    /** Runs a real ThreadPoolExecutor with tasks that block, and reports where they ended up. */
    static PoolMath.Outcome runReal(int core, int max, int capacity, int tasks) throws Exception {
        BlockingQueue<Runnable> queue = capacity == 0 ? new SynchronousQueue<>()
                : capacity == UNBOUNDED ? new LinkedBlockingQueue<>()
                : new ArrayBlockingQueue<>(capacity);
        ThreadPoolExecutor pool = new ThreadPoolExecutor(core, max, 1, TimeUnit.MINUTES, queue);
        CountDownLatch release = new CountDownLatch(1);
        AtomicInteger running = new AtomicInteger();
        int rejected = 0;
        try {
            for (int i = 0; i < tasks; i++) {
                try {
                    pool.execute(() -> {
                        running.incrementAndGet();
                        try { release.await(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                    });
                } catch (RejectedExecutionException e) {
                    rejected++;
                }
            }
            // every live thread is running exactly one task; wait until they have all started
            long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(10);
            while (running.get() < pool.getPoolSize() && System.nanoTime() < deadline) Thread.sleep(5);
            return new PoolMath.Outcome(pool.getPoolSize(), pool.getQueue().size(), rejected);
        } finally {
            release.countDown();
            pool.shutdown();
            pool.awaitTermination(10, TimeUnit.SECONDS);
        }
    }

    @ParameterizedTest(name = "core={0} max={1} queue={2} tasks={3} -> threads={4} queued={5} rejected={6}")
    @CsvSource({
            "2, 4, 2,          7, 4, 2, 1",
            "2, 4, 0,          7, 4, 0, 3",
            "2, 4, 2147483647, 7, 2, 5, 0",
            "1, 1, 1,          5, 1, 1, 3",
            "3, 3, 5,          6, 3, 3, 0",
            "2, 10, 3,        20, 10, 3, 7",
    })
    @DisplayName("predict() gives the known answer for each pool shape")
    void knownAnswers(int core, int max, int cap, int tasks, int threads, int queued, int rejected) {
        assertThat(PoolMath.predict(core, max, cap, tasks)).isEqualTo(new PoolMath.Outcome(threads, queued, rejected));
    }

    @Test
    @DisplayName("predict() agrees with a real ThreadPoolExecutor on 8 configurations")
    void matchesRealPool() throws Exception {
        int[][] configs = {
                {2, 4, 2, 7}, {2, 4, 0, 7}, {2, 4, UNBOUNDED, 7}, {1, 1, 1, 5},
                {3, 3, 5, 6}, {2, 10, 3, 20}, {4, 8, 16, 30}, {1, 6, 0, 4},
        };
        List<String> wrong = new ArrayList<>();
        for (int[] c : configs) {
            PoolMath.Outcome real = runReal(c[0], c[1], c[2], c[3]);
            PoolMath.Outcome predicted = PoolMath.predict(c[0], c[1], c[2], c[3]);
            if (!real.equals(predicted)) {
                wrong.add(String.format("core=%d max=%d queue=%d tasks=%d: real %s, predicted %s",
                        c[0], c[1], c[2], c[3], real, predicted));
            }
        }
        assertThat(wrong).as("configurations where the prediction was wrong").isEmpty();
    }

    @Test
    @DisplayName("AuthPool: 4 core, 8 max, queue of 16, 30 s keep-alive, AbortPolicy")
    void authPoolSettings() {
        ThreadPoolExecutor pool = AuthPool.create();
        try {
            assertThat(pool.getCorePoolSize()).as("core").isEqualTo(4);
            assertThat(pool.getMaximumPoolSize()).as("max").isEqualTo(8);
            assertThat(pool.getQueue().remainingCapacity()).as("queue capacity").isEqualTo(16);
            assertThat(pool.getKeepAliveTime(TimeUnit.SECONDS)).as("keep-alive seconds").isEqualTo(30);
            assertThat(pool.allowsCoreThreadTimeOut()).as("core threads time out").isFalse();
            assertThat(pool.getRejectedExecutionHandler()).isInstanceOf(ThreadPoolExecutor.AbortPolicy.class);
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    @DisplayName("AuthPool starts its 4 core threads before the first task arrives")
    void authPoolPrestarts() {
        ThreadPoolExecutor pool = AuthPool.create();
        try {
            assertThat(pool.getPoolSize()).as("threads before any task").isEqualTo(4);
        } finally {
            pool.shutdownNow();
        }
    }

    @Test
    @DisplayName("AuthPool accepts 24 blocking tasks and rejects the 25th")
    void authPoolRejectsOverflow() throws Exception {
        ThreadPoolExecutor pool = AuthPool.create();
        CountDownLatch release = new CountDownLatch(1);
        Runnable block = () -> { try { release.await(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } };
        try {
            for (int i = 0; i < 24; i++) pool.execute(block);
            assertThatThrownBy(() -> pool.execute(block)).isInstanceOf(RejectedExecutionException.class);
            assertThat(pool.getPoolSize()).as("threads").isEqualTo(8);
            assertThat(pool.getQueue()).as("queue").hasSize(16);
        } finally {
            release.countDown();
            pool.shutdown();
            pool.awaitTermination(10, TimeUnit.SECONDS);
        }
    }

    @Test
    @DisplayName("CountingRejectionHandler counts and throws with the pool's numbers")
    void handlerThrowsWithNumbers() throws Exception {
        CountingRejectionHandler handler = new CountingRejectionHandler();
        ThreadPoolExecutor pool = new ThreadPoolExecutor(1, 1, 1, TimeUnit.MINUTES, new ArrayBlockingQueue<>(2), handler);
        CountDownLatch started = new CountDownLatch(1);
        CountDownLatch release = new CountDownLatch(1);
        try {
            pool.execute(() -> {
                started.countDown();
                try { release.await(); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            });
            assertThat(started.await(5, TimeUnit.SECONDS)).isTrue();
            pool.execute(() -> { });
            pool.execute(() -> { });                       // the queue of 2 is now full
            assertThatThrownBy(() -> pool.execute(() -> { }))
                    .isInstanceOf(RejectedExecutionException.class)
                    .hasMessage("rejected: pool=1 active=1 queued=2");
            assertThatThrownBy(() -> pool.execute(() -> { })).isInstanceOf(RejectedExecutionException.class);
            assertThat(handler.rejected()).isEqualTo(2);
        } finally {
            release.countDown();
            pool.shutdown();
            pool.awaitTermination(10, TimeUnit.SECONDS);
        }
    }

    @Test
    @DisplayName("CountingRejectionHandler drops tasks quietly after shutdown, and still counts them")
    void handlerDropsAfterShutdown() throws Exception {
        CountingRejectionHandler handler = new CountingRejectionHandler();
        ThreadPoolExecutor pool = new ThreadPoolExecutor(1, 1, 1, TimeUnit.MINUTES, new ArrayBlockingQueue<>(2), handler);
        pool.shutdown();
        AtomicInteger ran = new AtomicInteger();
        pool.execute(ran::incrementAndGet);                // must not throw
        assertThat(pool.awaitTermination(10, TimeUnit.SECONDS)).isTrue();
        assertThat(ran.get()).as("dropped task ran").isZero();
        assertThat(handler.rejected()).isEqualTo(1);
    }
}
