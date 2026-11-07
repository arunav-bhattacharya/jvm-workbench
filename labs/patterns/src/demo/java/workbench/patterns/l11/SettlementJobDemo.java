package workbench.patterns.l11;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

/** Balking: eight triggers fire at once, and the settlement run refuses to start while one is in progress. */
public class SettlementJobDemo {

    static final class SettlementJob {
        private final AtomicBoolean running = new AtomicBoolean();

        boolean runIfIdle(Runnable settle) {
            if (!running.compareAndSet(false, true)) return false;      // balk: a run is already in progress
            try {
                settle.run();
                return true;
            } finally {
                running.set(false);
            }
        }
    }

    public static void main(String[] args) throws Exception {
        SettlementJob job = new SettlementJob();
        AtomicInteger inside = new AtomicInteger(), mostAtOnce = new AtomicInteger();
        AtomicInteger ran = new AtomicInteger(), balked = new AtomicInteger();
        Runnable settle = () -> {
            mostAtOnce.accumulateAndGet(inside.incrementAndGet(), Math::max);
            for (int i = 0; i < 2_000_000; i++) Thread.onSpinWait();   // settling takes a moment
            inside.decrementAndGet();
        };

        CountDownLatch go = new CountDownLatch(1);
        Thread[] triggers = new Thread[8];                              // the scheduler, a retry, an operator's button...
        for (int t = 0; t < triggers.length; t++) {
            triggers[t] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                if (job.runIfIdle(settle)) ran.incrementAndGet(); else balked.incrementAndGet();
            });
            triggers[t].start();
        }
        go.countDown();
        for (Thread t : triggers) t.join();
        System.out.println("ran " + ran + ", balked " + balked + ", most runs at once: " + mostAtOnce);
    }
}
