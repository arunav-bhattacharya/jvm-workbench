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

    public <T> T call(Supplier<T> op) {
        if (!permits.tryAcquire()) {                       // fail fast: never queue behind slow calls
            throw new BulkheadFull("at most " + maxConcurrent + " concurrent calls");
        }
        try {
            return op.get();
        } finally {
            permits.release();                             // always: a leaked permit shrinks the limit for good
        }
    }
}
