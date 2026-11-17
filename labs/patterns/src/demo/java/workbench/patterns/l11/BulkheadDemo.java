package workbench.patterns.l11;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;

/** 200 virtual threads book a courier whose booking line takes at most 20 calls at once: wait for a free line, or fail fast. */
public class BulkheadDemo {

    static void run(String mode, boolean failFast) throws InterruptedException {
        Semaphore permits = new Semaphore(20);
        AtomicInteger onLine = new AtomicInteger(), mostOnLine = new AtomicInteger();
        AtomicInteger done = new AtomicInteger(), rejected = new AtomicInteger();
        long start = System.nanoTime();
        try (ExecutorService ex = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 200; i++) {
                ex.submit(() -> {
                    if (failFast) {
                        if (!permits.tryAcquire()) { rejected.incrementAndGet(); return null; }   // bulkhead: busy tone, at once
                    } else {
                        permits.acquire();                                                      // limiter: wait on hold
                    }
                    try {
                        mostOnLine.accumulateAndGet(onLine.incrementAndGet(), Math::max);
                        Thread.sleep(20);                                                       // a booking takes 20 ms
                        onLine.decrementAndGet();
                        done.incrementAndGet();
                    } finally {
                        permits.release();
                    }
                    return null;
                });
            }
        }                                                                                       // close() waits for all tasks
        long ms = (System.nanoTime() - start) / 1_000_000;
        System.out.printf("%-10s done %3d, rejected %3d, most at once %2d, about %d ms%n",
                mode, done.get(), rejected.get(), mostOnLine.get(), ms);
    }

    public static void main(String[] args) throws InterruptedException {
        run("wait", false);
        run("fail fast", true);
    }
}
