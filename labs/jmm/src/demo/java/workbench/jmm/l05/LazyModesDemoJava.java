package workbench.jmm.l05;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

// Java has no `by lazy`. These are the closest Java equivalents of Kotlin's three LazyThreadSafetyMode values.
/** Eight threads read the same lazy value at the same moment, once for each kind of lazy. */
public class LazyModesDemoJava {

    // like SYNCHRONIZED: double-checked locking, so the initializer runs once
    static Supplier<Object> synchronizedLazy(Supplier<Object> init) {
        return new Supplier<>() {
            private volatile Object value;

            @Override
            public Object get() {
                Object v = value;
                if (v != null) return v;
                synchronized (this) {
                    if (value == null) value = init.get();
                    return value;
                }
            }
        };
    }

    // like PUBLICATION: any thread may compute, and the first compareAndSet wins
    static Supplier<Object> publicationLazy(Supplier<Object> init) {
        AtomicReference<Object> ref = new AtomicReference<>();
        return () -> {
            Object v = ref.get();
            if (v != null) return v;
            ref.compareAndSet(null, init.get());
            return ref.get();
        };
    }

    // like NONE: no synchronization at all, only safe on one thread
    static Supplier<Object> unsafeLazy(Supplier<Object> init) {
        Object[] box = new Object[1];
        return () -> {
            if (box[0] == null) box[0] = init.get();
            return box[0];
        };
    }

    public static void main(String[] args) throws InterruptedException {
        race("SYNCHRONIZED", LazyModesDemoJava::synchronizedLazy);
        race("PUBLICATION", LazyModesDemoJava::publicationLazy);
        race("NONE", LazyModesDemoJava::unsafeLazy);
    }

    interface LazyFactory { Supplier<Object> make(Supplier<Object> init); }

    static void race(String name, LazyFactory factory) throws InterruptedException {
        AtomicInteger runs = new AtomicInteger();
        Supplier<Object> signingKey = factory.make(() -> {
            runs.incrementAndGet();
            sleep(50);   // a slow initializer, like fetching a key from a vault
            return new Object();
        });

        Set<Object> seen = ConcurrentHashMap.newKeySet();
        CountDownLatch go = new CountDownLatch(1);
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(signingKey.get());
            });
            t.start();
            threads.add(t);
        }
        go.countDown();
        for (Thread t : threads) t.join();

        System.out.printf("%-12s initializer ran %d time(s), threads saw %d distinct value(s)%n", name, runs.get(), seen.size());
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
