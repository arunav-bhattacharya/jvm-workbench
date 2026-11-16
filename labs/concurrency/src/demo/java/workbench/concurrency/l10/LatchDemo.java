package workbench.concurrency.l10;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.TimeUnit;

/**
 * A shop's program loads three lists in parallel and opens its doors when all three are loaded.
 * Run with -Pargs=sleep to open after a fixed 250 ms nap instead, or -Pargs=stuck to make one load hang.
 */
public class LatchDemo {
    public static void main(String[] args) throws InterruptedException {
        String mode = args.length > 0 ? args[0] : "latch";
        String[] lists = {"price list", "stock counts", "today's offers"};
        long[] loadMs = {200, 400, mode.equals("stuck") ? 60_000 : 300};
        CountDownLatch loaded = new CountDownLatch(lists.length);
        long t0 = System.nanoTime();

        for (int i = 0; i < lists.length; i++) {
            String name = lists[i];
            long ms = loadMs[i];
            Thread t = new Thread(() -> {
                try {
                    Thread.sleep(ms);                                  // pretend to load
                    System.out.printf("%5d ms  %s loaded%n", (System.nanoTime() - t0) / 1_000_000, name);
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                } finally {
                    loaded.countDown();                                // count down even if loading failed
                }
            }, "load-" + i);
            t.setDaemon(true);
            t.start();
        }

        if (mode.equals("sleep")) {                                    // Naive: a guess about how long loading takes
            Thread.sleep(250);
            System.out.printf("%5d ms  doors open after a 250 ms nap, lists still loading: %d%n",
                    (System.nanoTime() - t0) / 1_000_000, loaded.getCount());
            return;
        }

        boolean ready = loaded.await(2, TimeUnit.SECONDS);             // never wait forever at startup
        System.out.printf("%5d ms  ready=%s, count=%d%n", (System.nanoTime() - t0) / 1_000_000, ready, loaded.getCount());

        // a latch is one-shot: once at zero, await() returns at once, forever
        if (ready) {
            loaded.countDown();
            System.out.println("after another countDown(): count=" + loaded.getCount()
                    + ", await returns at once: " + loaded.await(0, TimeUnit.MILLISECONDS));
        }
    }
}
