package workbench.vthreads.l06;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * 300 quote requests arrive at once. Each borrows a connection from a 10-connection pool for a
 * 5 ms query (the pool gives up after 30 ms of waiting), then makes a 100 ms FX call.
 * The same handler runs three ways: the old fixed pool, a plain swap to virtual threads,
 * and virtual threads with a Semaphore in front of the database.
 */
public class MigrationDemo {
    static final int REQUESTS = 300;
    static final int CONNECTIONS = 10;

    static final Semaphore pool = new Semaphore(CONNECTIONS);   // the fake connection pool
    static final AtomicInteger fxInFlight = new AtomicInteger();
    static final AtomicInteger fxPeak = new AtomicInteger();

    static String query() throws InterruptedException {
        if (!pool.tryAcquire(30, TimeUnit.MILLISECONDS)) {
            throw new IllegalStateException("connection pool: no connection after 30 ms");
        }
        try {
            Thread.sleep(5);                                     // the query
            return "standard";
        } finally {
            pool.release();
        }
    }

    static String fxRate() throws InterruptedException {
        fxPeak.accumulateAndGet(fxInFlight.incrementAndGet(), Math::max);
        try {
            Thread.sleep(100);                                   // the FX call
            return "1.0842";
        } finally {
            fxInFlight.decrementAndGet();
        }
    }

    interface Handler { String handle() throws Exception; }

    static void run(String label, ExecutorService executor, Handler handler) throws InterruptedException {
        fxPeak.set(0);
        int ok = 0, failed = 0;
        long t0 = System.nanoTime();
        try (executor) {
            List<Future<String>> futures = new ArrayList<>();
            for (int i = 0; i < REQUESTS; i++) futures.add(executor.submit(handler::handle));
            for (Future<String> f : futures) {
                try {
                    f.get();
                    ok++;
                } catch (ExecutionException e) {
                    failed++;
                }
            }
        }
        System.out.printf("%-34s %,6d ms   ok %3d   failed %3d   FX calls in flight at peak %3d%n",
                label, (System.nanoTime() - t0) / 1_000_000, ok, failed, fxPeak.get());
    }

    public static void main(String[] args) throws InterruptedException {
        // A: today: 10 platform threads, sized to the pool
        run("A: fixed pool of 10", Executors.newFixedThreadPool(10),
                () -> query() + fxRate());

        // B: the one-line migration: nothing limits the database any more
        run("B: virtual threads", Executors.newVirtualThreadPerTaskExecutor(),
                () -> query() + fxRate());

        // C: virtual threads, and the limit made explicit around the database call only
        Semaphore dbPermits = new Semaphore(CONNECTIONS, true);
        run("C: virtual threads + Semaphore(10)", Executors.newVirtualThreadPerTaskExecutor(), () -> {
            String tier;
            dbPermits.acquire();
            try {
                tier = query();
            } finally {
                dbPermits.release();
            }
            return tier + fxRate();
        });
    }
}
