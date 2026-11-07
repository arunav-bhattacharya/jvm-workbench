package workbench.executors.l09;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.LongAdder;

/** 10 tasks of 300 ms hit a pool of 2 threads with a queue of 4. Watch the numbers a dashboard would show. */
public class MetricsDemo {
    public static void main(String[] args) throws InterruptedException {
        LongAdder rejected = new LongAdder();
        ThreadPoolExecutor pool = new ThreadPoolExecutor(2, 2, 0, TimeUnit.MILLISECONDS, new ArrayBlockingQueue<>(4),
                Thread.ofPlatform().name("auth-", 0).factory(),
                (task, executor) -> {
                    rejected.increment();                                  // count it, then fail like AbortPolicy
                    throw new RejectedExecutionException("auth pool full");
                });

        for (int i = 0; i < 10; i++) {
            try {
                pool.execute(() -> sleep(300));
            } catch (RejectedExecutionException e) {
                // the caller would answer 503 here
            }
        }
        System.out.println("  ms  threads  active  queued  done  rejected");
        long t0 = System.nanoTime();
        for (int i = 0; i < 6; i++) {
            System.out.printf("%4d  %7d  %6d  %6d  %4d  %8d%n", (System.nanoTime() - t0) / 1_000_000,
                    pool.getPoolSize(), pool.getActiveCount(), pool.getQueue().size(),
                    pool.getCompletedTaskCount(), rejected.sum());
            sleep(200);
        }
        pool.shutdown();
        pool.awaitTermination(5, TimeUnit.SECONDS);
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
