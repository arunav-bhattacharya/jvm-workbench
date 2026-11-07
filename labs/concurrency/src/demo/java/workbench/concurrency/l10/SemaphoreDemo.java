package workbench.concurrency.l10;

import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;

/** 20 authorizations, 5 issuer permits, 100 ms per call. Then the bug that adds permits out of thin air. */
public class SemaphoreDemo {
    public static void main(String[] args) throws InterruptedException {
        Semaphore issuer = new Semaphore(5);
        AtomicInteger inFlight = new AtomicInteger(), peak = new AtomicInteger();
        Thread[] requests = new Thread[20];
        long t0 = System.nanoTime();
        for (int i = 0; i < requests.length; i++) {
            requests[i] = new Thread(() -> {
                try {
                    issuer.acquire();                                  // before the try
                    try {
                        peak.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                        Thread.sleep(100);                             // the call to the issuer
                        inFlight.decrementAndGet();
                    } finally {
                        issuer.release();
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
            requests[i].start();
        }
        for (Thread t : requests) t.join();
        System.out.printf("20 calls, peak in flight %d, took %d ms%n", peak.get(), (System.nanoTime() - t0) / 1_000_000);

        // permits belong to nobody: any thread can release, even one that never acquired
        Semaphore pool = new Semaphore(5);
        pool.release();
        System.out.println("new Semaphore(5), then one stray release(): " + pool.availablePermits() + " permits");
    }
}
