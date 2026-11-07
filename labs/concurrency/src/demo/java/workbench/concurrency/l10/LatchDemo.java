package workbench.concurrency.l10;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * A service warms three caches in parallel and opens for traffic when all three are loaded.
 * Run with -Pargs=stuck to make one warm-up hang.
 */
public class LatchDemo {
    public static void main(String[] args) throws InterruptedException {
        boolean stuck = args.length > 0 && args[0].equals("stuck");
        String[] caches = {"bin-ranges", "fx-rates", "merchant-config"};
        long[] loadMs = {200, 400, stuck ? 60_000 : 300};
        CountDownLatch warmedUp = new CountDownLatch(caches.length);
        long t0 = System.nanoTime();

        for (int i = 0; i < caches.length; i++) {
            String name = caches[i];
            long ms = loadMs[i];
            Thread t = new Thread(() -> {
                try {
                    Thread.sleep(ms);                                  // pretend to load
                    System.out.printf("%5d ms  %s loaded%n", (System.nanoTime() - t0) / 1_000_000, name);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    warmedUp.countDown();                              // count down even if loading failed
                }
            }, "warm-" + name);
            t.setDaemon(true);
            t.start();
        }

        boolean ready = warmedUp.await(2, TimeUnit.SECONDS);          // never wait forever at startup
        System.out.printf("%5d ms  ready=%s, count=%d%n", (System.nanoTime() - t0) / 1_000_000, ready, warmedUp.getCount());

        // a latch is one-shot: once at zero, await() returns at once, forever
        if (ready) {
            warmedUp.countDown();
            System.out.println("after another countDown(): count=" + warmedUp.getCount()
                    + ", await returns at once: " + warmedUp.await(0, TimeUnit.MILLISECONDS));
        }
    }
}
