package workbench.vthreads.l04;

import jdk.jfr.Recording;
import jdk.jfr.consumer.RecordedEvent;
import jdk.jfr.consumer.RecordingFile;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Duration;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;

import static org.assertj.core.api.Assertions.assertThat;

class TrapsTest {

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    /** A fake rates service: sleeps like an HTTP call and counts calls per pair. */
    static final class FakeRates implements Function<String, BigDecimal> {
        final Map<String, AtomicInteger> calls = new ConcurrentHashMap<>();
        final long latencyMs;
        FakeRates(long latencyMs) { this.latencyMs = latencyMs; }

        @Override public BigDecimal apply(String pair) {
            calls.computeIfAbsent(pair, k -> new AtomicInteger()).incrementAndGet();
            sleep(latencyMs);
            return new BigDecimal(pair.hashCode() % 1000).movePointLeft(3).abs().add(BigDecimal.ONE);
        }
    }

    @Test
    @DisplayName("FxRateCache loads each pair once when 200 virtual threads ask at the same time")
    void loadsOnce() throws Exception {
        FakeRates service = new FakeRates(50);
        FxRateCache cache = new FxRateCache(service);
        List<Future<BigDecimal>> results = new ArrayList<>();
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 200; i++) {
                String pair = i % 2 == 0 ? "EURUSD" : "GBPUSD";
                results.add(perTask.submit(() -> cache.rate(pair)));
            }
        }
        FakeRates expected = new FakeRates(0);
        for (int i = 0; i < 200; i++) {
            String pair = i % 2 == 0 ? "EURUSD" : "GBPUSD";
            assertThat(results.get(i).get()).isEqualByComparingTo(expected.apply(pair));
        }
        assertThat(service.calls.get("EURUSD").get()).as("calls to the rates service for EURUSD").isEqualTo(1);
        assertThat(service.calls.get("GBPUSD").get()).as("calls to the rates service for GBPUSD").isEqualTo(1);
        assertThat(cache.size()).isEqualTo(2);
    }

    @Test
    @DisplayName("FxRateCache never calls the rates service while holding the cache's monitor (synchronized)")
    void noMonitorAroundIo() {
        AtomicReference<FxRateCache> self = new AtomicReference<>();
        AtomicBoolean heldMonitor = new AtomicBoolean();
        FxRateCache cache = new FxRateCache(pair -> {
            if (Thread.holdsLock(self.get())) heldMonitor.set(true);
            return BigDecimal.ONE;
        });
        self.set(cache);
        cache.rate("EURUSD");
        cache.size();
        assertThat(heldMonitor).as("a synchronized monitor was held during the slow call").isFalse();
    }

    @Test
    @DisplayName("No virtual thread pins its carrier while the cache loads (JFR jdk.VirtualThreadPinned; catches pins on JDK 21 to 23)")
    void noPinnedEvents() throws Exception {
        // warm up first, so class loading doesn't show up in the recording
        FxRateCache warm = new FxRateCache(new FakeRates(1));
        Thread.ofVirtual().start(() -> warm.rate("WARMUP")).join();

        FxRateCache cache = new FxRateCache(new FakeRates(100));
        Path file = Files.createTempFile("vt04-pinning", ".jfr");
        try (Recording rec = new Recording()) {
            rec.enable("jdk.VirtualThreadPinned").withThreshold(Duration.ofMillis(20));
            rec.start();
            try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
                for (String pair : List.of("EURUSD", "GBPUSD", "USDJPY", "EURGBP")) {
                    perTask.submit(() -> cache.rate(pair));
                }
            }
            rec.stop();
            rec.dump(file);
        }
        List<RecordedEvent> pinned = RecordingFile.readAllEvents(file).stream()
                .filter(e -> e.getEventType().getName().equals("jdk.VirtualThreadPinned"))
                .toList();
        Files.deleteIfExists(file);
        assertThat(pinned).as("pinned events (JDK " + Runtime.version().feature() + ")").isEmpty();
    }

    @Test
    @DisplayName("ReceiptStamp formats UTC timestamps with milliseconds")
    void formats() {
        assertThat(ReceiptStamp.stamp(0)).isEqualTo("1970-01-01T00:00:00.000Z");
        assertThat(ReceiptStamp.stamp(1_773_480_413_589L)).isEqualTo("2026-03-14T09:26:53.589Z");
    }

    @Test
    @DisplayName("ReceiptStamp is correct when 10,000 virtual threads format at the same time")
    void formatsConcurrently() throws Exception {
        DateTimeFormatter expected = DateTimeFormatter.ofPattern("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'").withZone(ZoneOffset.UTC);
        List<Future<Boolean>> ok = new ArrayList<>();
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 10_000; i++) {
                long t = 1_700_000_000_000L + i * 86_400_123L;
                ok.add(perTask.submit(() -> ReceiptStamp.stamp(t).equals(expected.format(Instant.ofEpochMilli(t)))));
            }
        }
        int wrong = 0;
        for (Future<Boolean> f : ok) if (!f.get()) wrong++;
        assertThat(wrong).as("receipts with a garbled timestamp").isZero();
    }

    @Test
    @DisplayName("ReceiptStamp builds at most one formatter for 10,000 virtual threads (no per-thread cache)")
    void noPerThreadFormatters() throws Exception {
        ReceiptStamp.stamp(0);                         // let any one-time setup happen first
        int before = ReceiptStamp.formattersBuilt();
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < 10_000; i++) {
                long t = i;
                perTask.submit(() -> ReceiptStamp.stamp(t));
            }
        }
        assertThat(ReceiptStamp.formattersBuilt() - before).as("formatters built for 10,000 tasks").isLessThanOrEqualTo(1);
    }
}
