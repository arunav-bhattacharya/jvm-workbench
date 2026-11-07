package workbench.concurrency.l07;

import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;

/** A batch holds the ledger lock for 1.5 s. Three threads want in, each in a different way. */
public class TryLockDemo {
    static final ReentrantLock ledger = new ReentrantLock();
    static final Object monitor = new Object();

    public static void main(String[] args) throws InterruptedException {
        Thread batch = new Thread(() -> {
            ledger.lock();
            try {
                synchronized (monitor) {          // the batch holds the lock AND a monitor
                    pause(1_500);
                }
            } finally {
                ledger.unlock();
            }
        }, "batch");
        batch.start();
        Thread.sleep(100);                        // let the batch get in first

        Thread api = new Thread(() -> {
            long t0 = System.nanoTime();
            try {
                if (ledger.tryLock(200, TimeUnit.MILLISECONDS)) {      // wait at most 200 ms
                    try { System.out.println("api: got the lock"); } finally { ledger.unlock(); }
                } else {
                    System.out.printf("api: gave up after %d ms and answered 503%n", (System.nanoTime() - t0) / 1_000_000);
                }
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
        }, "api");

        Thread report = new Thread(() -> {
            try {
                ledger.lockInterruptibly();                            // an interrupt can cancel this wait
                try { System.out.println("report: got the lock"); } finally { ledger.unlock(); }
            } catch (InterruptedException e) {
                System.out.println("report: interrupted while waiting, gave up cleanly");
            }
        }, "report");

        Thread legacy = new Thread(() -> {
            synchronized (monitor) {                                   // no way to give up here
                System.out.println("legacy: got the monitor at last, interrupted=" + Thread.currentThread().isInterrupted());
            }
        }, "legacy");

        api.start();
        report.start();
        legacy.start();
        Thread.sleep(400);
        System.out.println("states: report=" + report.getState() + ", legacy=" + legacy.getState());
        report.interrupt();
        legacy.interrupt();
        for (Thread t : new Thread[] {api, report, legacy, batch}) t.join();
    }

    static void pause(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
