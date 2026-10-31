package workbench.concurrency.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicIntegerArray;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertTimeoutPreemptively;

class ExplicitLocksTest {

    private static Thread daemon(Runnable r) {
        Thread t = new Thread(r);
        t.setDaemon(true);
        t.start();
        return t;
    }

    private static boolean reachesWaiting(Thread t) throws InterruptedException {
        for (int i = 0; i < 500; i++) {
            if (t.getState() == Thread.State.WAITING || t.getState() == Thread.State.TIMED_WAITING) return true;
            Thread.sleep(10);
        }
        return false;
    }

    // ---------- LockBuffer ----------

    @Test
    @DisplayName("LockBuffer: first in, first out, and rejects a capacity below 1")
    void bufferFifo() throws Exception {
        LockBuffer<String> buffer = new LockBuffer<>(3);
        buffer.put("a");
        buffer.put("b");
        buffer.put("c");
        assertThat(buffer.size()).isEqualTo(3);
        assertThat(List.of(buffer.take(), buffer.take(), buffer.take())).containsExactly("a", "b", "c");
        assertThatThrownBy(() -> new LockBuffer<String>(0)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    @DisplayName("LockBuffer: take() parks while empty and returns when an item arrives")
    void bufferTakeWaits() throws Exception {
        LockBuffer<String> buffer = new LockBuffer<>(2);
        AtomicReference<String> got = new AtomicReference<>();
        Thread consumer = daemon(() -> {
            try { got.set(buffer.take()); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        });
        assertThat(reachesWaiting(consumer)).isTrue();
        buffer.put("auth-1");
        consumer.join(5_000);
        assertThat(got.get()).isEqualTo("auth-1");
    }

    @Test
    @DisplayName("LockBuffer: offer() gives up with false when the buffer stays full, true when there is room")
    void bufferOffer() throws Exception {
        LockBuffer<Integer> buffer = new LockBuffer<>(1);
        assertThat(buffer.offer(1, Duration.ofMillis(100))).isTrue();
        boolean second = assertTimeoutPreemptively(Duration.ofSeconds(5), () -> buffer.offer(2, Duration.ofMillis(200)));
        assertThat(second).as("offer into a full buffer").isFalse();
        assertThat(buffer.size()).isEqualTo(1);
    }

    @Test
    @DisplayName("LockBuffer: a waiting put() gives up with InterruptedException when interrupted")
    void bufferPutInterruptible() throws Exception {
        LockBuffer<Integer> buffer = new LockBuffer<>(1);
        buffer.put(1);
        AtomicReference<Throwable> thrown = new AtomicReference<>();
        Thread producer = daemon(() -> {
            try { buffer.put(2); } catch (Throwable e) { thrown.set(e); }
        });
        assertThat(reachesWaiting(producer)).isTrue();
        producer.interrupt();
        producer.join(5_000);
        assertThat(thrown.get()).isInstanceOf(InterruptedException.class);
    }

    @Test
    @DisplayName("LockBuffer: 4 producers and 4 consumers move 100,000 items through 4 slots, each exactly once")
    void bufferManyThreads() {
        assertTimeoutPreemptively(Duration.ofSeconds(15), () -> {
            LockBuffer<Integer> buffer = new LockBuffer<>(4);
            int perProducer = 25_000, total = 4 * perProducer;
            AtomicIntegerArray seen = new AtomicIntegerArray(total);
            List<Thread> threads = new ArrayList<>();
            for (int p = 0; p < 4; p++) {
                int base = p * perProducer;
                threads.add(daemon(() -> {
                    try { for (int i = 0; i < perProducer; i++) buffer.put(base + i); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                }));
            }
            for (int c = 0; c < 4; c++) {
                threads.add(daemon(() -> {
                    try { for (int i = 0; i < total / 4; i++) seen.incrementAndGet(buffer.take()); }
                    catch (InterruptedException e) { Thread.currentThread().interrupt(); }
                }));
            }
            for (Thread t : threads) t.join();
            for (int i = 0; i < total; i++) assertThat(seen.get(i)).as("times item %d was taken", i).isEqualTo(1);
        });
    }

    // ---------- FxRateCache ----------

    @Test
    @DisplayName("FxRateCache: loads a missing pair without hanging, then serves it from the cache")
    void cacheLoadsOnce() {
        AtomicInteger loads = new AtomicInteger();
        FxRateCache cache = new FxRateCache(pair -> { loads.incrementAndGet(); return new BigDecimal("1.0842"); });
        assertTimeoutPreemptively(Duration.ofSeconds(5), () -> {
            assertThat(cache.rate("EURUSD")).isEqualByComparingTo("1.0842");
            assertThat(cache.rate("EURUSD")).isEqualByComparingTo("1.0842");
        }, "rate() hung: did it ask for the write lock while holding the read lock?");
        assertThat(loads.get()).isEqualTo(1);
    }

    @Test
    @DisplayName("FxRateCache: 8 threads asking for the same missing pair call the loader exactly once")
    void cacheLoaderRunsOnce() {
        AtomicInteger loads = new AtomicInteger();
        FxRateCache cache = new FxRateCache(pair -> {
            loads.incrementAndGet();
            try { Thread.sleep(50); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            return new BigDecimal("0.9123");
        });
        assertTimeoutPreemptively(Duration.ofSeconds(10), () -> {
            CountDownLatch go = new CountDownLatch(1);
            List<Thread> threads = new ArrayList<>();
            for (int i = 0; i < 8; i++) {
                threads.add(daemon(() -> {
                    try { go.await(); } catch (InterruptedException e) { return; }
                    cache.rate("USDCHF");
                }));
            }
            go.countDown();
            for (Thread t : threads) t.join();
        }, "rate() hung: did it ask for the write lock while holding the read lock?");
        assertThat(loads.get()).as("loader calls for one pair").isEqualTo(1);
    }

    @Test
    @DisplayName("FxRateCache: snapshot() never mixes rates from two refreshes")
    void snapshotIsConsistent() throws Exception {
        FxRateCache cache = new FxRateCache(pair -> BigDecimal.ZERO);
        List<String> pairs = List.of("EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "EURGBP");
        Map<String, BigDecimal> ones = new HashMap<>(), twos = new HashMap<>();
        for (String p : pairs) { ones.put(p, BigDecimal.ONE); twos.put(p, BigDecimal.TWO); }
        cache.replaceAll(ones);

        AtomicBoolean done = new AtomicBoolean();
        List<Thread> refreshers = new ArrayList<>();
        for (int r = 0; r < 2; r++) {
            boolean start = r == 0;
            refreshers.add(daemon(() -> {
                boolean flip = start;
                while (!done.get()) {
                    cache.replaceAll(flip ? ones : twos);
                    flip = !flip;
                }
            }));
        }
        // up to 200,000 snapshots or 2 seconds, whichever comes first
        int mixed = 0;
        long deadline = System.nanoTime() + 2_000_000_000L;
        for (int i = 0; i < 200_000 && System.nanoTime() < deadline; i++) {
            Map<String, BigDecimal> snap = cache.snapshot(pairs);
            if (snap.values().stream().distinct().count() > 1) mixed++;
        }
        done.set(true);
        for (Thread t : refreshers) t.join(5_000);
        assertThat(mixed).as("snapshots that mixed two refreshes").isZero();
    }
}
