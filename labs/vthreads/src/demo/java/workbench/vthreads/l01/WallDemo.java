package workbench.vthreads.l01;

import java.time.Duration;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * Runs N fake "authorize a payment" requests that each block for a while,
 * first on a fixed pool, then with one virtual thread per request.
 *
 * <p>Args: pool size, number of requests, latency in ms. Default: 100 2000 100.
 */
public class WallDemo {
    public static void main(String[] args) {
        int poolSize = args.length > 0 ? Integer.parseInt(args[0]) : 100;
        int requests = args.length > 1 ? Integer.parseInt(args[1]) : 2_000;
        Duration latency = Duration.ofMillis(args.length > 2 ? Long.parseLong(args[2]) : 100);

        Runnable authorize = () -> {
            try {
                Thread.sleep(latency);          // stands in for the card issuer call
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        };

        long t0 = System.nanoTime();
        try (ExecutorService pool = Executors.newFixedThreadPool(poolSize)) {
            for (int i = 0; i < requests; i++) pool.execute(authorize);
        }
        report("fixed pool of " + poolSize, requests, t0);

        long t1 = System.nanoTime();
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < requests; i++) perTask.execute(authorize);
        }
        report("virtual thread per task", requests, t1);
    }

    static void report(String label, int requests, long startNanos) {
        long ms = (System.nanoTime() - startNanos) / 1_000_000;
        System.out.printf("%-26s %,6d requests in %,6d ms  = %,8.0f requests/s%n",
                label, requests, ms, requests * 1000.0 / Math.max(ms, 1));
    }
}
