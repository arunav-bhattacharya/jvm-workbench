// Java equivalent with virtual threads: one per request, and a java.util.concurrent.Semaphore as the bulkhead
package workbench.quotes.l03;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;

/** 40 requests at once to a provider that answers in 50 ms. How many calls does it see at once? Real time. */
public class BulkheadDemoJava {
    public static void main(String[] args) throws Exception {
        for (Integer limit : new Integer[] {null, 4}) {
            Semaphore permits = limit == null ? null : new Semaphore(limit);
            AtomicInteger active = new AtomicInteger();
            AtomicInteger peak = new AtomicInteger();
            Runnable call = () -> {
                peak.accumulateAndGet(active.incrementAndGet(), Math::max);
                try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                active.decrementAndGet();
            };
            long t0 = System.nanoTime();
            try (ExecutorService vthreads = Executors.newVirtualThreadPerTaskExecutor()) {
                for (int i = 0; i < 40; i++) {
                    vthreads.submit(() -> {
                        if (permits == null) { call.run(); return null; }
                        permits.acquire();                       // acquire before the try
                        try { call.run(); } finally { permits.release(); }
                        return null;
                    });
                }
            }                                                    // close() waits for all 40
            System.out.printf("%-9s calls in flight at most: %2d   all 40 answered after %3d ms%n",
                    limit == null ? "no limit" : "limit " + limit, peak.get(), (System.nanoTime() - t0) / 1_000_000);
        }
    }
}
