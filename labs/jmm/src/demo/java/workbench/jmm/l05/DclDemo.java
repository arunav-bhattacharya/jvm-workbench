package workbench.jmm.l05;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

/** Eight threads ask a hand-written double-checked lazy for the same value at the same moment. Edit it and rerun. */
public class DclDemo {

    static final class LazyCardTable {
        private volatile Object table;               // try: remove volatile
        private final AtomicInteger loads;

        LazyCardTable(AtomicInteger loads) { this.loads = loads; }

        Object get() {
            Object t = table;                        // 1. fast path: one volatile read, no lock
            if (t != null) return t;
            synchronized (this) {                    // 2. slow path: one thread at a time
                t = table;                           // 3. check again: another thread may have won
                if (t != null) return t;             //    (try deleting this line)
                loads.incrementAndGet();
                sleep(50);                           // reading the card table from a big file
                t = new Object();
                table = t;                           // 4. volatile write publishes the table
                return t;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            AtomicInteger loads = new AtomicInteger();
            LazyCardTable lazy = new LazyCardTable(loads);
            Set<Object> seen = ConcurrentHashMap.newKeySet();
            CountDownLatch ready = new CountDownLatch(8), go = new CountDownLatch(1);
            List<Thread> threads = new ArrayList<>();
            for (int i = 0; i < 8; i++) {
                Thread t = new Thread(() -> {
                    ready.countDown();
                    try { go.await(); } catch (InterruptedException e) { return; }
                    seen.add(lazy.get());
                });
                t.start();
                threads.add(t);
            }
            ready.await();
            go.countDown();
            for (Thread t : threads) t.join();
            System.out.printf("round %d: table loaded %d time(s), threads saw %d distinct table(s)%n", round, loads.get(), seen.size());
        }
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
