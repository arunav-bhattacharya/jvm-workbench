package workbench.ledger.l02.demo;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/**
 * A burst of 300 transfers hits a pool sized with Little's law: 8 threads, 80 queue slots, 5 ms
 * per transfer. Pass "callerRuns" to swap the counting abort policy for CallerRunsPolicy.
 */
public class BurstDemo {
    public static void main(String[] args) throws InterruptedException {
        boolean callerRuns = args.length > 0 && args[0].equals("callerRuns");
        AtomicInteger rejected = new AtomicInteger();
        RejectedExecutionHandler policy = callerRuns
                ? new ThreadPoolExecutor.CallerRunsPolicy()            // the submitting thread runs it itself
                : (task, pool) -> {                                    // count it, then throw at the caller
                    rejected.incrementAndGet();
                    throw new RejectedExecutionException("ledger pool full");
                };
        ThreadPoolExecutor pool = new ThreadPoolExecutor(8, 8, 0, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(80), Thread.ofPlatform().name("ledger-", 0).factory(), policy);
        pool.prestartAllCoreThreads();
        AtomicInteger ranOnCaller = new AtomicInteger();
        String caller = Thread.currentThread().getName();
        long t0 = System.nanoTime();
        int accepted = 0;
        for (int i = 0; i < 300; i++) {
            try {
                pool.execute(() -> {
                    if (Thread.currentThread().getName().equals(caller)) ranOnCaller.incrementAndGet();
                    sleep(5);                                          // the journal write
                });
                accepted++;
            } catch (RejectedExecutionException e) {
                // an HTTP handler would answer 503 with Retry-After here
            }
        }
        long submitMs = (System.nanoTime() - t0) / 1_000_000;
        pool.shutdown();
        pool.awaitTermination(10, TimeUnit.SECONDS);
        long doneMs = (System.nanoTime() - t0) / 1_000_000;
        System.out.printf("%s: accepted %d, rejected %d, run by the submitting thread %d%n",
                callerRuns ? "CallerRunsPolicy" : "counting abort", accepted, rejected.get(), ranOnCaller.get());
        System.out.printf("submitting took %d ms, all done after %d ms%n", submitMs, doneMs);
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
