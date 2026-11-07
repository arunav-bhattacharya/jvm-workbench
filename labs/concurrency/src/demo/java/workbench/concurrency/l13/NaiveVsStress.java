package workbench.concurrency.l13;

import java.util.concurrent.CountDownLatch;

/** The same racy counter, tested twice: the way most tests are written, and the way that finds the bug. */
public class NaiveVsStress {
    static final class Counter {
        volatile int count;                       // volatile only stops the JIT from hiding the race (lesson 3)
        void hit() { count++; }                   // the bug: read, add, write
    }

    // 2 threads, 1,000 hits each, no start line
    static boolean naiveRound() throws InterruptedException {
        Counter c = new Counter();
        Thread a = new Thread(() -> { for (int i = 0; i < 1_000; i++) c.hit(); });
        Thread b = new Thread(() -> { for (int i = 0; i < 1_000; i++) c.hit(); });
        a.start(); b.start();
        a.join(); b.join();
        return c.count == 2_000;
    }

    // 8 threads, 100,000 hits each, released together
    static boolean stressRound() throws InterruptedException {
        Counter c = new Counter();
        CountDownLatch go = new CountDownLatch(1);
        Thread[] ts = new Thread[8];
        for (int t = 0; t < ts.length; t++) {
            ts[t] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                for (int i = 0; i < 100_000; i++) c.hit();
            });
            ts[t].start();
        }
        go.countDown();
        for (Thread t : ts) t.join();
        return c.count == 800_000;
    }

    public static void main(String[] args) throws InterruptedException {
        int naiveFailed = 0, stressFailed = 0;
        for (int r = 0; r < 20; r++) if (!naiveRound()) naiveFailed++;
        for (int r = 0; r < 20; r++) if (!stressRound()) stressFailed++;
        System.out.println("naive test  (2 threads x 1,000, no start line): failed " + naiveFailed + " of 20 runs");
        System.out.println("stress test (8 threads x 100,000, start latch): failed " + stressFailed + " of 20 runs");
    }
}
