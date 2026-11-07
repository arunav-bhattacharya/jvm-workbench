package workbench.concurrency.l08;

/**
 * Tracks the largest authorization amount (in cents) seen so far, for a fraud dashboard.
 * Many request threads call {@link #offer} at once.
 *
 * <p>This version is check-then-act on a {@code volatile} field. Two threads can both read the
 * same old max and both "raise" it, and a smaller amount can overwrite a larger one.
 * Make {@link #offer} atomic WITHOUT {@code synchronized} or locks: hold the max in an
 * {@link java.util.concurrent.atomic.AtomicLong} and update it with a compare-and-set loop.
 */
public class MaxTracker {
    private volatile long max = Long.MIN_VALUE;

    /**
     * Records {@code amount}. Returns the max as it was just before this call
     * ({@link Long#MIN_VALUE} if nothing was recorded yet).
     */
    public long offer(long amount) {
        long prev = max;            // read
        if (amount > prev) {        // check
            max = amount;           // act: another thread may have raised max since the read
        }
        return prev;
    }

    /** The largest amount recorded so far, or {@link Long#MIN_VALUE}. */
    public long max() {
        return max;
    }
}
