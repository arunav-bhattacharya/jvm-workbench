package workbench.patterns.l11;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Balking: eight triggers fire at once, and the stock count refuses to start while one is already running. */
public class StockCountDemo {

    static final class StockCount {
        private final AtomicBoolean running = new AtomicBoolean();

        boolean runIfIdle(Runnable count) {
            if (!running.compareAndSet(false, true)) return false;      // balk: a count is already running
            try {
                count.run();
                return true;
            } finally {
                running.set(false);
            }
        }
    }

    public static void main(String[] args) throws Exception {
        StockCount stockCount = new StockCount();
        AtomicInteger inside = new AtomicInteger(), mostAtOnce = new AtomicInteger();
        AtomicInteger ran = new AtomicInteger(), balked = new AtomicInteger();
        Runnable count = () -> {
            mostAtOnce.accumulateAndGet(inside.incrementAndGet(), Math::max);
            for (int i = 0; i < 2_000_000; i++) Thread.onSpinWait();   // counting the shelves takes a moment
            inside.decrementAndGet();
        };

        CountDownLatch go = new CountDownLatch(1);
        Thread[] triggers = new Thread[8];                              // the closing-time timer, the manager's button, a retry...
        for (int t = 0; t < triggers.length; t++) {
            triggers[t] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                if (stockCount.runIfIdle(count)) ran.incrementAndGet(); else balked.incrementAndGet();
            });
            triggers[t].start();
        }
        go.countDown();
        for (Thread t : triggers) t.join();
        System.out.println("ran " + ran + ", balked " + balked + ", most counts at once: " + mostAtOnce);
    }
}
