package workbench.patterns.l01;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

/**
 * Java has no `by lazy`, so here are the three Kotlin modes written by hand.
 * Eight threads read the value for the first time, together. Count the initializer runs.
 */
public class LazyModesJava {
    interface Lazy<T> { T get(); }

    // SYNCHRONIZED: double-checked locking; the initializer runs once
    static final class SynchronizedLazy<T> implements Lazy<T> {
        private final Supplier<T> init;
        private volatile T value;
        SynchronizedLazy(Supplier<T> init) { this.init = init; }
        public T get() {
            T v = value;
            if (v == null) {
                synchronized (this) {
                    v = value;
                    if (v == null) value = v = init.get();
                }
            }
            return v;
        }
    }

    // PUBLICATION: no lock; every racer computes, compareAndSet keeps the first stored value
    static final class PublicationLazy<T> implements Lazy<T> {
        private final Supplier<T> init;
        private final AtomicReference<T> value = new AtomicReference<>();
        PublicationLazy(Supplier<T> init) { this.init = init; }
        public T get() {
            T v = value.get();
            if (v != null) return v;
            value.compareAndSet(null, init.get());
            return value.get();
        }
    }

    // NONE: a plain field, no guarantees across threads
    static final class UnsafeLazy<T> implements Lazy<T> {
        private final Supplier<T> init;
        private T value;
        UnsafeLazy(Supplier<T> init) { this.init = init; }
        public T get() {
            if (value == null) value = init.get();
            return value;
        }
    }

    public static void main(String[] args) throws InterruptedException {
        trial("SYNCHRONIZED", SynchronizedLazy::new);
        trial("PUBLICATION", PublicationLazy::new);
    }

    static void trial(String mode, java.util.function.Function<Supplier<Map<String, Double>>, Lazy<Map<String, Double>>> make)
            throws InterruptedException {
        AtomicInteger runs = new AtomicInteger();
        Lazy<Map<String, Double>> rates = make.apply(() -> {
            runs.incrementAndGet();
            try { Thread.sleep(20); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return Map.of("EUR/USD", 1.08);
        });
        Set<Object> seen = Collections.synchronizedSet(Collections.newSetFromMap(new IdentityHashMap<>()));
        CountDownLatch go = new CountDownLatch(1);
        Thread[] ts = new Thread[8];
        for (int i = 0; i < ts.length; i++) {
            ts[i] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(rates.get());
            });
            ts[i].start();
        }
        go.countDown();
        for (Thread t : ts) t.join();
        System.out.printf("%-12s initializer ran %d time(s), callers saw %d instance(s)%n", mode, runs.get(), seen.size());
    }
}
