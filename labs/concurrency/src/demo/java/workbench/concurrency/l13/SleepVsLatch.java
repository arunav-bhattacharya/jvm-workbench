package workbench.concurrency.l13;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * A test checks that a background worker settles a payment. One version sleeps 3 ms and hopes;
 * the other waits on a latch. Both run 100 times while 8 threads keep every core busy, like a CI box.
 */
public class SleepVsLatch {
    static volatile boolean burn = true;

    // the code under test: settles on another thread, about 2 ms of work
    static Thread settleAsync(Runnable whenDone) {
        Thread t = new Thread(() -> {
            long end = System.nanoTime() + 2_000_000;
            while (System.nanoTime() < end) Thread.onSpinWait();
            whenDone.run();
        });
        t.start();
        return t;
    }

    public static void main(String[] args) throws InterruptedException {
        for (int i = 0; i < 8; i++) {
            Thread b = new Thread(() -> { while (burn) Thread.onSpinWait(); });   // a busy machine
            b.setDaemon(true);
            b.start();
        }
        int sleepFailed = 0, latchFailed = 0;
        for (int run = 0; run < 100; run++) {
            boolean[] settled = {false};
            Thread t = settleAsync(() -> settled[0] = true);
            Thread.sleep(3);                                   // "should be enough"
            if (!settled[0]) sleepFailed++;                    // (a racy read too, which is the point)
            t.join();
        }
        for (int run = 0; run < 100; run++) {
            CountDownLatch settled = new CountDownLatch(1);
            settleAsync(settled::countDown);
            if (!settled.await(5, TimeUnit.SECONDS)) latchFailed++;   // waits exactly as long as needed
        }
        burn = false;
        System.out.println("sleep(3) then assert:  failed " + sleepFailed + " of 100");
        System.out.println("latch.await(5 s):      failed " + latchFailed + " of 100");
    }
}
