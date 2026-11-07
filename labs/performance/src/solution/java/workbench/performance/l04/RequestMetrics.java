package workbench.performance.l04;

import java.util.concurrent.atomic.LongAdder;

public final class RequestMetrics {
    // many writers, rare reads: LongAdder spreads the writes over padded cells (Striped64.Cell)
    private final LongAdder count = new LongAdder();
    private final LongAdder totalCents = new LongAdder();

    public void record(long amountCents) {
        count.increment();
        totalCents.add(amountCents);
    }

    // sum() adds up the cells; it is not an atomic snapshot of both counters, which is fine for metrics
    public long count() { return count.sum(); }

    public long totalCents() { return totalCents.sum(); }
}
