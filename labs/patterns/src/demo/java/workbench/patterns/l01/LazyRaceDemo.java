package workbench.patterns.l01;

import java.util.Collections;
import java.util.IdentityHashMap;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/** Eight threads ask for a "singleton" at the same moment. How many get built? */
public class LazyRaceDemo {
    static final AtomicInteger built = new AtomicInteger();

    static final class FxRates {
        FxRates() {
            built.incrementAndGet();
            try { Thread.sleep(20); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }  // a slow load
        }
    }

    // broken: check-then-act on a plain static field
    static FxRates racy;
    static FxRates racyGet() {
        if (racy == null) racy = new FxRates();
        return racy;
    }

    // initialization-on-demand holder: the JVM runs Holder's static init once, under its class-init lock
    static final class Holder { static final FxRates INSTANCE = new FxRates(); }
    static FxRates holderGet() { return Holder.INSTANCE; }

    public static void main(String[] args) throws InterruptedException {
        report("racy check-then-act", LazyRaceDemo::racyGet);
        report("holder idiom       ", LazyRaceDemo::holderGet);
    }

    static void report(String name, Supplier<FxRates> get) throws InterruptedException {
        built.set(0);
        Set<Object> seen = Collections.synchronizedSet(Collections.newSetFromMap(new IdentityHashMap<>()));
        CountDownLatch go = new CountDownLatch(1);
        Thread[] ts = new Thread[8];
        for (int i = 0; i < ts.length; i++) {
            ts[i] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(get.get());
            });
            ts[i].start();
        }
        go.countDown();
        for (Thread t : ts) t.join();
        System.out.printf("%s: constructor ran %d time(s), callers saw %d instance(s)%n", name, built.get(), seen.size());
    }
}
