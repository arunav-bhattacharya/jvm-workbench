package workbench.jmm.l05;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;

/** Eight threads ask a hand-written double-checked lazy for the same value at the same moment. Edit it and rerun. */
public class DclDemo {

    static final class LazySigningKey {
        private volatile Object key;                 // try: remove volatile
        private final AtomicInteger loads;

        LazySigningKey(AtomicInteger loads) { this.loads = loads; }

        Object get() {
            Object k = key;                          // 1. fast path: one volatile read, no lock
            if (k != null) return k;
            synchronized (this) {                    // 2. slow path: one thread at a time
                k = key;                             // 3. check again: another thread may have won
                if (k != null) return k;             //    (try deleting this line)
                loads.incrementAndGet();
                sleep(50);                           // fetching a signing key from a vault
                k = new Object();
                key = k;                             // 4. volatile write publishes the key
                return k;
            }
        }
    }

    public static void main(String[] args) throws InterruptedException {
        for (int round = 1; round <= 3; round++) {
            AtomicInteger loads = new AtomicInteger();
            LazySigningKey lazy = new LazySigningKey(loads);
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
            System.out.printf("round %d: key loaded %d time(s), threads saw %d distinct key(s)%n", round, loads.get(), seen.size());
        }
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
