package workbench.vthreads.l03;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 1,000 requests arrive at once. The database allows 20 calls at once, each takes 50 ms.
 * A request waits at most 200 ms for a permit, then gives up (a fast "busy, try again" instead of a slow timeout).
 *
 * <p>Args: permits, call ms, max wait ms. Default: 20 50 200.
 */
public class ShedLoadDemo {
    public static void main(String[] args) {
        int permits = args.length > 0 ? Integer.parseInt(args[0]) : 20;
        long callMs = args.length > 1 ? Long.parseLong(args[1]) : 50;
        long maxWaitMs = args.length > 2 ? Long.parseLong(args[2]) : 200;

        Semaphore db = new Semaphore(permits);
        AtomicInteger served = new AtomicInteger();
        AtomicInteger shed = new AtomicInteger();
        long t0 = System.nanoTime();
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 1_000; i++) {
                perTask.execute(() -> {
                    try {
                        if (!db.tryAcquire(maxWaitMs, TimeUnit.MILLISECONDS)) {
                            shed.incrementAndGet();        // no permit in time: fail fast
                            return;
                        }
                        try {
                            Thread.sleep(callMs);          // the database call
                            served.incrementAndGet();
                        } finally {
                            db.release();
                        }
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    }
                });
            }
        }
        System.out.printf("permits=%d call=%d ms max wait=%d ms: served %d, shed %d, in %d ms%n",
                permits, callMs, maxWaitMs, served.get(), shed.get(), (System.nanoTime() - t0) / 1_000_000);
    }
}
