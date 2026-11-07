package workbench.patterns.l11;

import java.util.concurrent.Semaphore;
import java.util.function.Supplier;

/**
 * A semaphore bulkhead: at most {@code maxConcurrent} calls run against one dependency at once.
 * A call over the limit fails fast with {@link BulkheadFull}; it never waits for a permit.
 */
public final class Bulkhead {

    /** Thrown when every permit is taken. */
    public static final class BulkheadFull extends RuntimeException {
        public BulkheadFull(String message) { super(message); }
    }

    private final int maxConcurrent;
    private final Semaphore permits;

    public Bulkhead(int maxConcurrent) {
        this.maxConcurrent = maxConcurrent;
        this.permits = new Semaphore(maxConcurrent);
    }

    /** Free permits right now. Given. */
    public int available() {
        return permits.availablePermits();
    }

    /** Runs {@code op} if a permit is free, otherwise throws BulkheadFull at once. Always gives the permit back. */
    public <T> T call(Supplier<T> op) {
        throw new UnsupportedOperationException("TODO: tryAcquire, run op, release in finally");
    }
}
