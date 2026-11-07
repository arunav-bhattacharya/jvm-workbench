package workbench.container.l01.demo;

import workbench.container.l01.SingletonCell;

import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Supplier;

/** Eight threads ask for the same singleton at the same moment, three ways. */
public class SingletonRaceDemo {
    static final AtomicInteger CONSTRUCTED = new AtomicInteger();

    public static class FxRates {
        public FxRates() {
            CONSTRUCTED.incrementAndGet();
            try { Thread.sleep(20); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }   // loads a rate table
        }
    }

    public static void main(String[] args) throws Exception {
        Map<Class<?>, Object> beans = new ConcurrentHashMap<>();
        race("check-then-act on a map", () -> {
            Object bean = beans.get(FxRates.class);          // check
            if (bean == null) {
                bean = new FxRates();                        // act: every thread that saw null gets here
                beans.put(FxRates.class, bean);
            }
            return bean;
        });

        SingletonCell<FxRates> cell = new SingletonCell<>(FxRates::new);
        race("SingletonCell", cell::get);

        // computeIfAbsent can't build a graph: the function must not touch the same map
        for (String[] edge : new String[][] {{"paymentService", "feeCalculator"}, {"payouts", "ledger"}}) {
            Map<String, Object> byName = new ConcurrentHashMap<>();
            try {
                byName.computeIfAbsent(edge[0], k -> List.of(byName.computeIfAbsent(edge[1], k2 -> new Object())));
                System.out.printf("computeIfAbsent, %s needs %s: worked%n", edge[0], edge[1]);
            } catch (IllegalStateException e) {
                System.out.printf("computeIfAbsent, %s needs %s: %s%n", edge[0], edge[1], e);
            }
        }
    }

    static void race(String name, Supplier<Object> get) throws InterruptedException {
        CONSTRUCTED.set(0);
        CountDownLatch go = new CountDownLatch(1);
        Set<Object> seen = java.util.Collections.synchronizedSet(java.util.Collections.newSetFromMap(new IdentityHashMap<>()));
        List<Thread> threads = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            Thread t = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                seen.add(get.get());
            });
            t.start();
            threads.add(t);
        }
        go.countDown();                                       // all eight start together
        for (Thread t : threads) t.join();
        System.out.printf("%-24s constructor ran %d times, threads saw %d instance(s)%n", name, CONSTRUCTED.get(), seen.size());
    }
}
