package workbench.concurrency.l10;

import java.util.concurrent.Semaphore;
import java.util.concurrent.atomic.AtomicInteger;

/** 20 card checks, 5 permits, a slow web service that takes 120 ms per call. Then the bug that adds permits out of thin air. */
public class SemaphoreDemo {
    public static void main(String[] args) throws InterruptedException {
        Semaphore bank = new Semaphore(5);                             // the bank's service allows 5 calls at once
        AtomicInteger inFlight = new AtomicInteger(), peak = new AtomicInteger();
        Thread[] requests = new Thread[20];
        long t0 = System.nanoTime();
        for (int i = 0; i < requests.length; i++) {
            requests[i] = new Thread(() -> {
                try {
                    bank.acquire();                                    // before the try
                    try {
                        peak.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                        Thread.sleep(120);                             // the call to the slow web service
                        inFlight.decrementAndGet();
                    } finally {
                        bank.release();
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
        Semaphore carPark = new Semaphore(5);
        carPark.release();
        System.out.println("new Semaphore(5), then one stray release(): " + carPark.availablePermits() + " permits");
    }
}
