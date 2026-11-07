package workbench.concurrency.l07;

import java.util.concurrent.locks.StampedLock;

/**
 * A writer keeps moving an FX quote; the ask is always bid + 2. A reader reads both fields
 * optimistically for one second and counts how often validate() caught a half-written quote.
 */
public class OptimisticRead {
    static final StampedLock lock = new StampedLock();
    static long bid = 100, ask = 102;                 // guarded by lock; ask == bid + 2 when no write is in progress
    static volatile boolean done;

    public static void main(String[] args) throws InterruptedException {
        Thread writer = new Thread(() -> {
            long v = 100;
            while (!done) {
                long stamp = lock.writeLock();
                try {
                    bid = ++v;
                    for (int i = 0; i < 20; i++) Thread.onSpinWait();   // widens the half-written moment
                    ask = v + 2;
                } finally {
                    lock.unlockWrite(stamp);
                }
            }
        });
        writer.start();

        long reads = 0, failed = 0, tornCaught = 0, tornPassed = 0;
        long end = System.nanoTime() + 1_000_000_000L;
        while (System.nanoTime() < end) {
            reads++;
            long stamp = lock.tryOptimisticRead();     // 1. no lock taken, just a version number
            long b = bid, a = ask;                     // 2. copy the fields into locals
            boolean torn = a - b != 2;
            if (lock.validate(stamp)) {                // 3. did a writer get in since step 1?
                if (torn) tornPassed++;                //    never happens
            } else {
                failed++;
                if (torn) tornCaught++;
                stamp = lock.readLock();               // 4. fall back to a real read lock
                try { b = bid; a = ask; } finally { lock.unlockRead(stamp); }
            }
        }
        done = true;
        writer.join();
        System.out.printf("reads: %,d   failed validate(): %,d   torn quotes caught: %,d   torn quotes that passed validate(): %d%n",
                reads, failed, tornCaught, tornPassed);
    }
}
