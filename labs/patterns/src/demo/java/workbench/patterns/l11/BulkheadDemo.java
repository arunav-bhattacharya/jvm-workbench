package workbench.patterns.l11;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;

/** 200 virtual threads call a PSP that should see at most 20 at once: wait for a permit, or fail fast. */
public class BulkheadDemo {

    static void run(String mode, boolean failFast) throws InterruptedException {
        Semaphore permits = new Semaphore(20);
        AtomicInteger inFlight = new AtomicInteger(), mostInFlight = new AtomicInteger();
        AtomicInteger done = new AtomicInteger(), rejected = new AtomicInteger();
        long start = System.nanoTime();
        try (ExecutorService ex = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 200; i++) {
                ex.submit(() -> {
                    if (failFast) {
                        if (!permits.tryAcquire()) { rejected.incrementAndGet(); return null; }   // bulkhead: reject now
                    } else {
                        permits.acquire();                                                      // limiter: wait in line
                    }
                    try {
                        mostInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                        Thread.sleep(20);                                                       // the PSP takes 20 ms
                        inFlight.decrementAndGet();
                        done.incrementAndGet();
                    } finally {
                        permits.release();
                    }
                    return null;
                });
            }
        }                                                                                       // close() waits for all tasks
        long ms = (System.nanoTime() - start) / 1_000_000;
        System.out.printf("%-10s done %3d, rejected %3d, most in flight %2d, about %d ms%n",
                mode, done.get(), rejected.get(), mostInFlight.get(), ms);
    }

    public static void main(String[] args) throws InterruptedException {
        run("wait", false);
        run("fail fast", true);
    }
}
