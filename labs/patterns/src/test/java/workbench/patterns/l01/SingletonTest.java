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
    private static final Map<String, String> NETWORKS = Map.of(
            "VISA", "https://sandbox.visa.example",
            "MASTERCARD", "https://sandbox.mc.example");

    /** A loader that counts its calls and takes 50 ms, like reading files and calling a config service. */
    private static Supplier<Map<String, String>> slowLoader(AtomicInteger calls) {
        return () -> {
            calls.incrementAndGet();
            sleep(50);
            return new HashMap<>(NETWORKS);   // a fresh map each call, so two loads give two instances
        };
    }

    // the registry tests use their own start line, so a bug in your Contention doesn't hide their results
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
    @DisplayName("The registry loads nothing until the first lookup")
    void lazy() {
        AtomicInteger calls = new AtomicInteger();
        CardNetworkRegistry registry = new CardNetworkRegistry(slowLoader(calls));
        assertThat(registry.isLoaded()).isFalse();
        assertThat(calls.get()).isZero();
        assertThat(registry.sandboxUrl("VISA")).isEqualTo("https://sandbox.visa.example");
        assertThat(registry.isLoaded()).isTrue();
        assertThat(calls.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("8 threads doing the first lookup together run the loader exactly once")
    void loadsOnceUnderContention() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        CardNetworkRegistry registry = new CardNetworkRegistry(slowLoader(calls));
        together(THREADS, () -> registry.sandboxUrl("MASTERCARD"));
        assertThat(calls.get()).as("loader calls").isEqualTo(1);
    }

    @Test
    @DisplayName("Every thread gets the same table instance")
    void sameTableForEveryone() throws Exception {
        CardNetworkRegistry registry = new CardNetworkRegistry(slowLoader(new AtomicInteger()));
        AtomicReference<Map<String, String>> first = new AtomicReference<>();
        AtomicInteger different = new AtomicInteger();
        together(THREADS, () -> {
            Map<String, String> t = registry.table();
            if (!first.compareAndSet(null, t) && first.get() != t) different.incrementAndGet();
        });
        assertThat(different.get()).as("threads that saw a different instance").isZero();
        assertThat(registry.table()).isSameAs(first.get());
    }

    @Test
    @DisplayName("A failed load is not cached: the next call runs the loader again")
    void failedLoadRetries() {
        AtomicInteger calls = new AtomicInteger();
        CardNetworkRegistry registry = new CardNetworkRegistry(() -> {
            if (calls.incrementAndGet() == 1) throw new IllegalStateException("config service down");
            return NETWORKS;
        });
        assertThatThrownBy(() -> registry.sandboxUrl("VISA")).isInstanceOf(IllegalStateException.class);
        assertThat(registry.isLoaded()).isFalse();
        assertThat(registry.sandboxUrl("VISA")).isEqualTo("https://sandbox.visa.example");
        assertThat(calls.get()).isEqualTo(2);
    }

    @Test
    @DisplayName("An unknown network is an IllegalArgumentException")
    void unknownNetwork() {
        CardNetworkRegistry registry = new CardNetworkRegistry(() -> NETWORKS);
        assertThatThrownBy(() -> registry.sandboxUrl("AMEX"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessageContaining("AMEX");
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
    @DisplayName("Your registry passes your harness: one table instance across 8 threads")
    void registryPassesHarness() throws Exception {
        CardNetworkRegistry registry = new CardNetworkRegistry(slowLoader(new AtomicInteger()));
        assertThat(Contention.distinctInstances(THREADS, registry::table)).isEqualTo(1);
    }
}
