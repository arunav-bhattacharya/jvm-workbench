package workbench.ledger.l03.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.locks.ReentrantLock;

/**
 * One carrier thread. 20 virtual threads pay a hot merchant account while a ticker tries to tick
 * every 10 ms. Where the journal write sits decides whether the carrier stays free.
 */
public class LockScopeDemoJava {
    static final Object merchantMonitor = new Object();       // a hot merchant account, guarded by a monitor...
    static final ReentrantLock merchantLock = new ReentrantLock();   // ...or by a ReentrantLock
    static long merchantBalance = 0;
    static volatile long longestGap;

    static void journalWrite() {                              // 20 ms of blocking I/O
        try {
            Thread.sleep(20);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        System.setProperty("jdk.virtualThreadScheduler.parallelism", "1");   // before the first virtual thread
        System.out.println("JDK " + Runtime.version() + ", 1 carrier thread");
        runVariant("journal inside synchronized   ", () -> {
            synchronized (merchantMonitor) { journalWrite(); merchantBalance += 100; }
        });
        runVariant("journal inside ReentrantLock  ", () -> {
            merchantLock.lock();
            try { journalWrite(); merchantBalance += 100; } finally { merchantLock.unlock(); }
        });
        runVariant("journal first, then the lock  ", () -> {
            journalWrite();
            merchantLock.lock();
            try { merchantBalance += 100; } finally { merchantLock.unlock(); }
        });
    }

    static void runVariant(String label, Runnable transfer) throws InterruptedException {
        longestGap = 0;
        Thread ticker = Thread.ofVirtual().start(() -> {
            long last = System.nanoTime();
            for (int i = 0; i < 40; i++) {
                try { Thread.sleep(10); } catch (InterruptedException e) { return; }
                long now = System.nanoTime();
                longestGap = Math.max(longestGap, (now - last) / 1_000_000);
                last = now;
            }
        });
        Thread.sleep(5);
        long t0 = System.nanoTime();
        List<Thread> payers = new ArrayList<>();
        for (int i = 0; i < 20; i++) payers.add(Thread.ofVirtual().start(transfer));
        for (Thread p : payers) p.join();
        long ms = (System.nanoTime() - t0) / 1_000_000;
        ticker.join();
        System.out.printf("%s 20 transfers in %4d ms, longest gap between ticks: %3d ms%n", label, ms, longestGap);
    }
}
