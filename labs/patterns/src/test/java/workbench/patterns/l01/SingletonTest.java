package workbench.patterns.l01;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.BrokenBarrierException;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.CyclicBarrier;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class SingletonTest {
    private static final int THREADS = 8;
    private static final Map<String, Long> PRICES = Map.of(
            "BREAD", 450L,
            "MILK", 120L);

    /** A loader that counts its calls and takes 50 ms, like reading the supplier's price file. */
    private static Supplier<Map<String, Long>> slowLoader(AtomicInteger calls) {
        return () -> {
            calls.incrementAndGet();
            sleep(50);
            return new HashMap<>(PRICES);   // a fresh map each call, so two loads give two instances
        };
    }

    // the price list tests use their own start line, so a bug in your Contention doesn't hide their results
    private static void together(int threads, Runnable task) throws InterruptedException {
        CountDownLatch go = new CountDownLatch(1);
        Thread[] ts = new Thread[threads];
        for (int i = 0; i < threads; i++) {
            ts[i] = new Thread(() -> {
                try { go.await(); } catch (InterruptedException e) { return; }
                task.run();
            });
            ts[i].start();
        }
        go.countDown();
        for (Thread t : ts) t.join();
    }

    private static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }

    @Test
    @DisplayName("The price list loads nothing until the first lookup")
    void lazy() {
        AtomicInteger calls = new AtomicInteger();
        PriceList priceList = new PriceList(slowLoader(calls));
        assertThat(priceList.isLoaded()).isFalse();
        assertThat(calls.get()).isZero();
        assertThat(priceList.priceOf("BREAD")).isEqualTo(450);
        assertThat(priceList.isLoaded()).isTrue();
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("8 threads doing the first lookup together run the loader exactly once")
    void loadsOnceUnderContention() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        PriceList priceList = new PriceList(slowLoader(calls));
        together(THREADS, () -> priceList.priceOf("MILK"));
        assertThat(calls.get()).as("loader calls").isEqualTo(1);
    }

    @Test
    @DisplayName("Every thread gets the same map instance")
    void samePricesForEveryone() throws Exception {
        PriceList priceList = new PriceList(slowLoader(new AtomicInteger()));
        AtomicReference<Map<String, Long>> first = new AtomicReference<>();
        AtomicInteger different = new AtomicInteger();
        together(THREADS, () -> {
            Map<String, Long> p = priceList.prices();
            if (!first.compareAndSet(null, p) && first.get() != p) different.incrementAndGet();
        });
        assertThat(different.get()).as("threads that saw a different instance").isZero();
        assertThat(priceList.prices()).isSameAs(first.get());
    }

    @Test
    @DisplayName("A failed load is not cached: the next call runs the loader again")
    void failedLoadRetries() {
        AtomicInteger calls = new AtomicInteger();
        PriceList priceList = new PriceList(() -> {
            if (calls.incrementAndGet() == 1) throw new IllegalStateException("price file not found");
            return PRICES;
        });
        assertThatThrownBy(() -> priceList.priceOf("BREAD")).isInstanceOf(IllegalStateException.class);
        assertThat(priceList.isLoaded()).isFalse();
        assertThat(priceList.priceOf("BREAD")).isEqualTo(450);
        assertThat(calls.get()).isEqualTo(2);
    }

    @Test
    @DisplayName("An unknown product is an IllegalArgumentException")
    void unknownProduct() {
        PriceList priceList = new PriceList(() -> PRICES);
        assertThatThrownBy(() -> priceList.priceOf("CAVIAR"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("CAVIAR");
    }

    @Test
    @DisplayName("Contention counts 1 for a supplier that always returns the same object")
    void harnessCountsOne() throws Exception {
        Object only = new Object();
        assertThat(Contention.distinctInstances(THREADS, () -> only)).isEqualTo(1);
    }

    @Test
    @DisplayName("Contention counts by identity, not equals: 8 empty lists are 8 instances")
    void harnessCountsByIdentity() throws Exception {
        assertThat(Contention.distinctInstances(THREADS, ArrayList::new)).isEqualTo(THREADS);
    }

    @Test
    @DisplayName("Contention releases the threads together, so their calls overlap")
    void harnessOverlaps() throws Exception {
        // each call waits at a barrier for all the others; it only returns a fresh object if they all met
        CyclicBarrier allHere = new CyclicBarrier(THREADS);
        Object loner = new Object();
        int n = Contention.distinctInstances(THREADS, () -> {
            try {
                allHere.await(3, TimeUnit.SECONDS);
                return new Object();
            } catch (InterruptedException | BrokenBarrierException | TimeoutException e) {
                return loner;
            }
        });
        assertThat(n).isEqualTo(THREADS);
    }

    @Test
    @DisplayName("Contention catches a racy lazy singleton building more than one instance")
    void harnessCatchesRacyLazy() throws Exception {
        // a deliberately broken lazy holder: check-then-act with a slow constructor
        class RacyLazy {
            private Object instance;
            Object get() {
                if (instance == null) { sleep(50); instance = new Object(); }
                return instance;
            }
        }
        RacyLazy racy = new RacyLazy();
        assertThat(Contention.distinctInstances(THREADS, racy::get)).isGreaterThan(1);
    }

    @Test
    @DisplayName("Your price list passes your harness: one map instance across 8 threads")
    void priceListPassesHarness() throws Exception {
        PriceList priceList = new PriceList(slowLoader(new AtomicInteger()));
        assertThat(Contention.distinctInstances(THREADS, priceList::prices)).isEqualTo(1);
    }
}
