package workbench.vthreads.l01;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;

/**
 * Starts N threads that all block on one latch, so they exist at the same time,
 * then releases them. First with platform threads, then with virtual threads.
 *
 * <p>Args: platform count, virtual count. Default: 4000 100000.
 * Keep the platform count at 5,000 or below on a laptop.
 */
public class ThreadCostDemo {
    public static void main(String[] args) throws InterruptedException {
        int platform = args.length > 0 ? Integer.parseInt(args[0]) : 4_000;
        int virtual = args.length > 1 ? Integer.parseInt(args[1]) : 100_000;
        time("platform", platform, Thread.ofPlatform());
        time("virtual", virtual, Thread.ofVirtual());
    }

    static void time(String kind, int n, Thread.Builder builder) throws InterruptedException {
        CountDownLatch release = new CountDownLatch(1);
        List<Thread> threads = new ArrayList<>(n);
        long t0 = System.nanoTime();
        for (int i = 0; i < n; i++) {
            threads.add(builder.start(() -> {
                try {
                    release.await();            // every thread stays alive until we let go
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            }));
        }
        long startedMs = (System.nanoTime() - t0) / 1_000_000;
        release.countDown();
        for (Thread t : threads) t.join();
        long totalMs = (System.nanoTime() - t0) / 1_000_000;
        System.out.printf("%-8s %,7d threads alive at once: started in %,5d ms, all finished after %,5d ms (%.1f us per thread)%n",
                kind, n, startedMs, totalMs, totalMs * 1000.0 / n);
    }
}
