package workbench.performance.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.openjdk.jol.info.ClassLayout;
import org.openjdk.jol.info.FieldLayout;

import java.util.concurrent.CountDownLatch;

import static org.assertj.core.api.Assertions.assertThat;

class CacheLineTest {
    private static final int CACHE_LINE = 64;

    private static long offsetOf(Class<?> type, String field) {
        return ClassLayout.parseClass(type).fields().stream()
                .filter(f -> f.name().equals(field))
                .mapToLong(FieldLayout::offset)
                .findFirst()
                .orElseThrow(() -> new AssertionError("no field named " + field + " in " + type.getSimpleName()));
    }

    // start all threads together, so they really run at the same time
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

    @Test
    @DisplayName("StageCounters keeps parsed and written at least 64 bytes apart (real offsets, read with JOL)")
    void countersAreOnDifferentLines() {
        long parsed = offsetOf(StageCounters.class, "parsed");
        long written = offsetOf(StageCounters.class, "written");
        // a distance, not absolute offsets: object headers differ between JDKs and flags
        assertThat(Math.abs(written - parsed)).as("bytes between parsed (at %d) and written (at %d)", parsed, written)
                .isGreaterThanOrEqualTo(CACHE_LINE);
    }

    @Test
    @DisplayName("StageCounters still counts exactly with one writer thread per counter")
    void stageCountsAreExact() throws InterruptedException {
        StageCounters c = new StageCounters();
        Thread parser = new Thread(() -> { for (int i = 0; i < 1_000_000; i++) c.addParsed(); });
        Thread writer = new Thread(() -> { for (int i = 0; i < 1_000_000; i++) c.addWritten(); });
        parser.start(); writer.start();
        parser.join(); writer.join();
        assertThat(c.parsed()).isEqualTo(1_000_000);
        assertThat(c.written()).isEqualTo(1_000_000);
    }

    @Test
    @DisplayName("RequestMetrics counts every request when 8 threads record 200,000 each")
    void metricsCountIsExact() throws InterruptedException {
        RequestMetrics m = new RequestMetrics();
        together(8, () -> { for (int i = 0; i < 200_000; i++) m.record(5); });
        assertThat(m.count()).as("requests counted").isEqualTo(8 * 200_000L);
    }

    @Test
    @DisplayName("RequestMetrics adds up every word count when 8 threads record at once")
    void metricsTotalIsExact() throws InterruptedException {
        RequestMetrics m = new RequestMetrics();
        together(8, () -> { for (int i = 0; i < 200_000; i++) m.record(250); });
        assertThat(m.totalWords()).as("total words").isEqualTo(8 * 200_000L * 250);
    }
}
