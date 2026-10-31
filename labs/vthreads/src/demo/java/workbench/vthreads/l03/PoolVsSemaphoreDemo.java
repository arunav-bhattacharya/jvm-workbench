package workbench.vthreads.l03;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;

/**
 * Each request calls the fraud service (60 ms, no limit) and then the ledger database
 * (10 ms, at most 20 at once). Two ways to respect the database limit:
 * a pool of 20 virtual threads, or one virtual thread per request plus a Semaphore(20).
 */
public class PoolVsSemaphoreDemo {
    static final int REQUESTS = 1_000;
    static final int DB_LIMIT = 20;

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) {
        // A: the anti-pattern. The pool size limits the database, and also everything else.
        long t0 = System.nanoTime();
        try (ExecutorService pool = Executors.newFixedThreadPool(DB_LIMIT, Thread.ofVirtual().factory())) {
            for (int i = 0; i < REQUESTS; i++) {
                pool.execute(() -> {
                    sleep(60);                      // fraud check: needs no limit
                    sleep(10);                      // ledger write: needs the limit
                });
            }
        }
        System.out.printf("pool of %d virtual threads:        %,5d ms%n", DB_LIMIT, (System.nanoTime() - t0) / 1_000_000);

        // B: one virtual thread per request; the semaphore guards only the database call
        Semaphore db = new Semaphore(DB_LIMIT);
        long t1 = System.nanoTime();
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < REQUESTS; i++) {
                perTask.execute(() -> {
                    sleep(60);                      // all 1,000 fraud checks overlap
                    try {
                        db.acquire();               // at most 20 inside the database
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                        return;
                    }
                    try {
                        sleep(10);
                    } finally {
                        db.release();
                    }
                });
            }
        }
        System.out.printf("virtual thread per task + Semaphore(%d): %,5d ms%n", DB_LIMIT, (System.nanoTime() - t1) / 1_000_000);
    }
}
