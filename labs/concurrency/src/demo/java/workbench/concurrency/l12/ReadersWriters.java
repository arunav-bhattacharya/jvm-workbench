package workbench.concurrency.l12;

import java.util.concurrent.locks.ReentrantReadWriteLock;

/**
 * Four readers keep a rate table busy for 1.5 s, overlapping all the time. One writer wants in once.
 * How long does it wait with a hand-written readers-first lock, and with ReentrantReadWriteLock?
 */
public class ReadersWriters {
    interface RW { void readLock() throws InterruptedException; void readUnlock(); void writeLock() throws InterruptedException; void writeUnlock(); }

    /** The textbook readers-first lock: a reader may enter whenever no writer is INSIDE. */
    static final class ReadersFirst implements RW {
        private int readers;
        private boolean writing;
        public synchronized void readLock() throws InterruptedException { while (writing) wait(); readers++; }
        public synchronized void readUnlock() { if (--readers == 0) notifyAll(); }
        public synchronized void writeLock() throws InterruptedException { while (writing || readers > 0) wait(); writing = true; }
        public synchronized void writeUnlock() { writing = false; notifyAll(); }
    }

    static final class Jdk implements RW {
        private final ReentrantReadWriteLock rw = new ReentrantReadWriteLock();
        public void readLock() { rw.readLock().lock(); }
        public void readUnlock() { rw.readLock().unlock(); }
        public void writeLock() { rw.writeLock().lock(); }
        public void writeUnlock() { rw.writeLock().unlock(); }
    }

    static long writerWaitMs(RW lock) throws InterruptedException {
        long end = System.nanoTime() + 1_500_000_000L;
        Thread[] readers = new Thread[4];
        for (int i = 0; i < readers.length; i++) {
            readers[i] = new Thread(() -> {
                try {
                    while (System.nanoTime() < end) {
                        lock.readLock();
                        try { Thread.sleep(2); } finally { lock.readUnlock(); }   // a 2 ms read
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                }
            });
            readers[i].start();
            Thread.sleep(1);                                  // stagger them so they overlap
        }
        Thread.sleep(100);
        long t0 = System.nanoTime();
        lock.writeLock();                                     // the refresh wants in
        long waited = (System.nanoTime() - t0) / 1_000_000;
        lock.writeUnlock();
        for (Thread r : readers) r.join();
        return waited;
    }

    public static void main(String[] args) throws InterruptedException {
        System.out.println("readers-first lock:     writer waited " + writerWaitMs(new ReadersFirst()) + " ms");
        System.out.println("ReentrantReadWriteLock: writer waited " + writerWaitMs(new Jdk()) + " ms");
    }
}
