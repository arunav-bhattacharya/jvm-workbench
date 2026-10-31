package workbench.executors.l03;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;

/**
 * 200 requests that each wait 50 ms on a downstream call, on pools of 5, 10, 20 and 40 threads.
 * Little's law predicts throughput = threads / 0.05 s. Pass "db" to make every request also hold
 * one of only 10 database connections while it waits.
 */
public class LittlesLawDemo {
    public static void main(String[] args) throws Exception {
        boolean db = args.length > 0 && args[0].equals("db");
        Semaphore connections = new Semaphore(10);          // a 10-connection pool, when "db" is on
        int requests = 200;
        double latencySeconds = 0.050;
        for (int threads : new int[] {5, 10, 20, 40}) {
            long t0 = System.nanoTime();
            try (ExecutorService pool = Executors.newFixedThreadPool(threads)) {
                for (int i = 0; i < requests; i++) {
                    pool.execute(() -> {
                        try {
                            if (db) connections.acquire();
                            try {
                                Thread.sleep(50);           // the downstream call
                            } finally {
                                if (db) connections.release();
                            }
                        } catch (InterruptedException e) {
                            Thread.currentThread().interrupt();
                        }
                    });
                }
            }
            double seconds = (System.nanoTime() - t0) / 1e9;
            System.out.printf("%2d threads: %4.0f req/s measured, %4.0f predicted by threads / W%n",
                    threads, requests / seconds, threads / latencySeconds);
        }
    }
}
