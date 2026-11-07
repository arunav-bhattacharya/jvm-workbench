package workbench.concurrency.l09;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Consumer;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class ConcurrentCollectionsTest {

    /** Starts one daemon thread per task behind a start latch, joins them, and rethrows the first failure. */
    private static void collide(List<Runnable> tasks) throws Exception {
        CountDownLatch go = new CountDownLatch(1);
        AtomicReference<Throwable> failure = new AtomicReference<>();
        List<Thread> threads = new ArrayList<>();
        for (Runnable task : tasks) {
            Thread t = new Thread(() -> {
                try {
                    go.await();
                    task.run();
                } catch (Throwable e) {
                    failure.compareAndSet(null, e);
                }
            });
            t.setDaemon(true);
            t.start();
            threads.add(t);
        }
        go.countDown();
        for (Thread t : threads) t.join(10_000);
        if (failure.get() != null) throw new AssertionError("a thread failed: " + failure.get(), failure.get());
    }

    // ---------- BinCache ----------

    @Test
    @DisplayName("BinCache: 8 requests for the same new BIN call the slow loader exactly once")
    void binLoadedOnce() throws Exception {
        AtomicInteger loads = new AtomicInteger();
        BinCache cache = new BinCache(bin -> {
            loads.incrementAndGet();
            try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return "Northwind Bank";
        });
        Map<String, String> answers = new ConcurrentHashMap<>();
        List<Runnable> tasks = new ArrayList<>();
        for (int i = 0; i < 8; i++) {
            int me = i;
            tasks.add(() -> answers.put("t" + me, cache.issuerFor("411111")));
        }
        collide(tasks);
        assertThat(loads.get()).as("loader calls for one BIN").isEqualTo(1);
        assertThat(answers.values()).hasSize(8).containsOnly("Northwind Bank");
    }

    @Test
    @DisplayName("BinCache: each BIN is loaded once and then served from the cache")
    void binsCachedSeparately() {
        Map<String, AtomicInteger> loads = new ConcurrentHashMap<>();
        BinCache cache = new BinCache(bin -> {
            loads.computeIfAbsent(bin, b -> new AtomicInteger()).incrementAndGet();
            return "issuer-of-" + bin;
        });
        for (int round = 0; round < 3; round++) {
            assertThat(cache.issuerFor("411111")).isEqualTo("issuer-of-411111");
            assertThat(cache.issuerFor("550000")).isEqualTo("issuer-of-550000");
        }
        assertThat(cache.size()).isEqualTo(2);
        assertThat(loads.get("411111").get()).isEqualTo(1);
        assertThat(loads.get("550000").get()).isEqualTo(1);
    }

    @Test
    @DisplayName("BinCache: a loader that throws caches nothing, so the next request tries again")
    void failedLoadNotCached() {
        AtomicInteger calls = new AtomicInteger();
        BinCache cache = new BinCache(bin -> {
            if (calls.incrementAndGet() == 1) throw new IllegalStateException("directory timed out");
            return "Northwind Bank";
        });
        assertThatThrownBy(() -> cache.issuerFor("411111")).isInstanceOf(IllegalStateException.class);
        assertThat(cache.size()).isZero();
        assertThat(cache.issuerFor("411111")).isEqualTo("Northwind Bank");
    }

    // ---------- WebhookRegistry ----------

    @Test
    @DisplayName("WebhookRegistry: a listener can unregister itself while an event is being published")
    void listenerRemovesItself() {
        WebhookRegistry registry = new WebhookRegistry();
        List<String> received = new CopyOnWriteArrayList<>();
        Consumer<String>[] once = new Consumer[1];
        once[0] = e -> { received.add("once:" + e); registry.unregister(once[0]); };
        registry.register(once[0]);
        registry.register(e -> received.add("always:" + e));

        registry.publish("pay-1");
        registry.publish("pay-2");

        assertThat(received).containsExactly("once:pay-1", "always:pay-1", "always:pay-2");
        assertThat(registry.count()).isEqualTo(1);
    }

    @Test
    @DisplayName("WebhookRegistry: 4 threads register 2,000 listeners each while 4 threads publish; nothing throws, nothing is lost")
    void registerWhilePublishing() throws Exception {
        WebhookRegistry registry = new WebhookRegistry();
        AtomicInteger deliveries = new AtomicInteger();
        CountDownLatch registered = new CountDownLatch(4);
        List<Runnable> tasks = new ArrayList<>();
        for (int i = 0; i < 4; i++) {
            tasks.add(() -> {
                for (int n = 0; n < 2_000; n++) registry.register(e -> deliveries.incrementAndGet());
                registered.countDown();
            });
            tasks.add(() -> {
                while (registered.getCount() > 0) registry.publish("pay");
            });
        }
        collide(tasks);
        assertThat(registry.count()).as("listeners kept").isEqualTo(8_000);
        deliveries.set(0);
        registry.publish("final");
        assertThat(deliveries.get()).isEqualTo(8_000);
    }

    // ---------- Batcher ----------

    @Test
    @DisplayName("Batcher: nextBatch() returns up to max entries at once, oldest first")
    void batchesInOrder() throws Exception {
        Batcher<Integer> b = new Batcher<>(100);
        for (int i = 1; i <= 7; i++) assertThat(b.submit(i)).isTrue();
        assertThat(b.nextBatch(5, Duration.ofSeconds(1))).containsExactly(1, 2, 3, 4, 5);
        assertThat(b.nextBatch(5, Duration.ofSeconds(1))).containsExactly(6, 7);
        assertThat(b.pending()).isZero();
    }

    @Test
    @DisplayName("Batcher: submit() returns false at once when the queue is full; capacity below 1 is rejected")
    void submitWhenFull() {
        Batcher<String> b = new Batcher<>(2);
        assertThat(b.submit("a")).isTrue();
        assertThat(b.submit("b")).isTrue();
        boolean third = assertTimeoutPreemptively(Duration.ofSeconds(2), () -> b.submit("c"), "submit() blocked on a full queue");
        assertThat(third).isFalse();
        assertThat(b.pending()).isEqualTo(2);
        assertThatThrownBy(() -> new Batcher<String>(0)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    @DisplayName("Batcher: nextBatch() waits for the first entry, and returns an empty batch if none arrives in time")
    void batchWaits() throws Exception {
        Batcher<String> b = new Batcher<>(10);
        long t0 = System.nanoTime();
        assertThat(b.nextBatch(10, Duration.ofMillis(200))).isEmpty();
        assertThat((System.nanoTime() - t0) / 1_000_000).as("ms waited for nothing").isGreaterThanOrEqualTo(100);

        AtomicReference<List<String>> got = new AtomicReference<>();
        Thread writer = new Thread(() -> {
            try { got.set(b.nextBatch(10, Duration.ofSeconds(10))); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        writer.setDaemon(true);
        writer.start();
        Thread.sleep(100);
        b.submit("entry-1");
        writer.join(5_000);
        assertThat(got.get()).containsExactly("entry-1");
    }
}
