package workbench.patterns.l01;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.function.Supplier;

public final class Contention {
    private Contention() {}

    public static int distinctInstances(int threads, Supplier<?> supplier) throws InterruptedException {
        CountDownLatch ready = new CountDownLatch(threads);
        CountDownLatch go = new CountDownLatch(1);
        // results by thread number; a plain array is fine because join() makes the writes visible
        Object[] results = new Object[threads];
        Thread[] ts = new Thread[threads];
        for (int i = 0; i < threads; i++) {
            int slot = i;
            ts[i] = new Thread(() -> {
                ready.countDown();                       // 1. "I'm at the start line"
                try {
                    go.await();                          // 2. wait for the starting gun
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    return;
                }
                results[slot] = supplier.get();          // 3. everyone calls at the same moment
            });
            ts[i].start();
        }
        ready.await();
        go.countDown();
        for (Thread t : ts) t.join();                    // 4. join: results are now visible here

        // 5. count by identity (==), not equals: an IdentityHashMap-backed set
        Set<Object> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        for (Object r : results) seen.add(r);
        return seen.size();
    }
}
