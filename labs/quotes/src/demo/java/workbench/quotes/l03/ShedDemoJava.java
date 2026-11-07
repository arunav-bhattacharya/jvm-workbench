// Java equivalent with virtual threads: Semaphore.tryAcquire() sheds, a timed tryAcquire is the deadline
package workbench.quotes.l03;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;

/**
 * A burst of 500 requests. The provider takes 10 calls at a time, 50 ms each, and every request
 * has a 300 ms deadline. Queue them all, or shed what can't make the deadline? Real time.
 */
public class ShedDemoJava {
    public static void main(String[] args) throws Exception {
        for (Integer maxInFlight : new Integer[] {null, 50}) {
            Semaphore provider = new Semaphore(10);
            Semaphore admission = maxInFlight == null ? null : new Semaphore(maxInFlight);
            AtomicInteger live = new AtomicInteger(), late = new AtomicInteger(), busy = new AtomicInteger();
            AtomicLong waitedForNothing = new AtomicLong();
            try (ExecutorService vthreads = Executors.newVirtualThreadPerTaskExecutor()) {
                for (int i = 0; i < 500; i++) {
                    vthreads.submit(() -> {
                        if (admission != null && !admission.tryAcquire()) { busy.incrementAndGet(); return null; }   // ERR busy
                        long start = System.nanoTime();
                        try {
                            long deadline = start + TimeUnit.MILLISECONDS.toNanos(300);
                            if (provider.tryAcquire(300, TimeUnit.MILLISECONDS)) {
                                try { Thread.sleep(50); } finally { provider.release(); }
                                if (System.nanoTime() <= deadline) { live.incrementAndGet(); return null; }
                            }
                            late.incrementAndGet();
                            waitedForNothing.addAndGet((System.nanoTime() - start) / 1_000_000);
                        } finally {
                            if (admission != null) admission.release();
                        }
                        return null;
                    });
                }
            }
            System.out.printf("%-14s live answers: %3d   missed the deadline: %3d   shed as busy: %3d   ms spent waiting for nothing: %,d%n",
                    maxInFlight == null ? "queue them all" : "admit " + maxInFlight, live.get(), late.get(), busy.get(), waitedForNothing.get());
        }
    }
}
