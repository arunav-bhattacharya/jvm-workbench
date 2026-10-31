// Java equivalent of BlockingBudgets.kt: the same 400 blocking calls on a 64-thread pool,
// a pool that grows as needed, and one virtual thread per call.
package workbench.coroutines.l04;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

public class BlockingBudgetsJava {
    static void runBlockingCalls(String label, ExecutorService pool) {
        AtomicInteger active = new AtomicInteger();
        AtomicInteger peak = new AtomicInteger();
        long t0 = System.nanoTime();
        try (pool) {   // close() waits for all 400 calls
            for (int i = 0; i < 400; i++) {
                pool.submit(() -> {
                    peak.accumulateAndGet(active.incrementAndGet(), Math::max);
                    try { Thread.sleep(200); } catch (InterruptedException e) { return; }  // a blocking issuer call
                    active.decrementAndGet();
                });
            }
        }
        System.out.printf("%-32s %5d ms, peak %3d calls at once%n", label, (System.nanoTime() - t0) / 1_000_000, peak.get());
    }

    public static void main(String[] args) {
        runBlockingCalls("fixed pool of 64", Executors.newFixedThreadPool(64));
        runBlockingCalls("cached pool (grows)", Executors.newCachedThreadPool());
        runBlockingCalls("virtual thread per task", Executors.newVirtualThreadPerTaskExecutor());
    }
}
