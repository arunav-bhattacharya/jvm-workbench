package workbench.concurrency.l08;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicLong;

/** A hand-written compare-and-set increment. Count how often the CAS fails as threads are added. */
public class CasRetries {
    static final AtomicLong counter = new AtomicLong();

    // returns how many times compareAndSet failed before it worked
    static long increment() {
        long failures = 0;
        while (true) {
            long seen = counter.get();                         // 1. read
            if (counter.compareAndSet(seen, seen + 1)) {       // 2. write only if still `seen`
                return failures;
            }
            failures++;                                        // 3. someone else won: retry
        }
    }

    public static void main(String[] args) throws InterruptedException {
        int perThread = 1_000_000;
        for (int threads : new int[] {1, 2, 4, 8}) {
            counter.set(0);
            AtomicLong failed = new AtomicLong();
            CountDownLatch go = new CountDownLatch(1);           // start them all together
            List<Thread> ts = new ArrayList<>();
            for (int i = 0; i < threads; i++) {
                ts.add(new Thread(() -> {
                    try { go.await(); } catch (InterruptedException e) { return; }
                    long mine = 0;
                    for (int n = 0; n < perThread; n++) mine += increment();
                    failed.addAndGet(mine);
                }));
            }
            for (Thread t : ts) t.start();
            go.countDown();
            for (Thread t : ts) t.join();
            System.out.printf("threads: %d  counter: %,10d  failed CAS: %,10d  (%.2f per increment)%n",
                    threads, counter.get(), failed.get(), failed.get() / (double) counter.get());
        }
    }
}
