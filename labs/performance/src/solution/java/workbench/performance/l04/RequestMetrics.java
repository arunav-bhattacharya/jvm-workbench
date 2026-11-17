package workbench.performance.l04;

import java.util.concurrent.atomic.LongAdder;

public final class RequestMetrics {
    // many writers, rare reads: LongAdder spreads the writes over padded cells (Striped64.Cell)
    private final LongAdder count = new LongAdder();
    private final LongAdder totalWords = new LongAdder();

    public void record(long words) {
        count.increment();
        totalWords.add(words);
    }

    // sum() adds up the cells; it is not an atomic snapshot of both counters, which is fine for metrics
    public long count() { return count.sum(); }

    public long totalWords() { return totalWords.sum(); }
}
