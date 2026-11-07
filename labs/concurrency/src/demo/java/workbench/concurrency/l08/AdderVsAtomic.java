package workbench.concurrency.l08;

import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.LongAdder;

/** 8 threads each count 2,000,000 events: once on one AtomicLong, once on a LongAdder. */
public class AdderVsAtomic {
    static long time(Runnable perThreadWork) throws InterruptedException {
        Thread[] ts = new Thread[8];
        for (int i = 0; i < ts.length; i++) ts[i] = new Thread(perThreadWork);
        long t0 = System.nanoTime();
        for (Thread t : ts) t.start();
        for (Thread t : ts) t.join();
        return (System.nanoTime() - t0) / 1_000_000;
    }

    public static void main(String[] args) throws InterruptedException {
        int n = 2_000_000;
        for (int round = 1; round <= 3; round++) {
            AtomicLong atomic = new AtomicLong();
            LongAdder adder = new LongAdder();
            long a = time(() -> { for (int i = 0; i < n; i++) atomic.incrementAndGet(); });
            long b = time(() -> { for (int i = 0; i < n; i++) adder.increment(); });
            System.out.printf("round %d: AtomicLong %,d in %4d ms   LongAdder %,d in %4d ms%n",
                    round, atomic.get(), a, adder.sum(), b);
        }
    }
}
