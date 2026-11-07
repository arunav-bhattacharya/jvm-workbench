package workbench.performance.l04;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;

/** Four threads count 10 million requests each, into one AtomicLong and then into one LongAdder. */
public class AdderDemo {
    static final int THREADS = 4, PER_THREAD = 10_000_000;

    static long time(Runnable perThread) throws InterruptedException {
        CountDownLatch go = new CountDownLatch(1);
        Thread[] ts = new Thread[THREADS];
        for (int i = 0; i < THREADS; i++) {
            ts[i] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                perThread.run();
            });
            ts[i].start();
        }
        long t0 = System.nanoTime();
        go.countDown();
        for (Thread t : ts) t.join();
        return (System.nanoTime() - t0) / 1_000_000;
    }

    public static void main(String[] args) throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            AtomicLong atomic = new AtomicLong();
            long msAtomic = time(() -> { for (int i = 0; i < PER_THREAD; i++) atomic.incrementAndGet(); });
            LongAdder adder = new LongAdder();
            long msAdder = time(() -> { for (int i = 0; i < PER_THREAD; i++) adder.increment(); });
            System.out.printf("round %d: AtomicLong %,5d ms (%,d)   LongAdder %,5d ms (%,d)%n",
                    round, msAtomic, atomic.get(), msAdder, adder.sum());
        }
    }
}
