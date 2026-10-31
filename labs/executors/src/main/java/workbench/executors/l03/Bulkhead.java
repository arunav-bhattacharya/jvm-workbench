package workbench.executors.l03;

import java.time.Duration;
import java.util.concurrent.Callable;
import java.util.concurrent.Semaphore;

/**
 * A bulkhead: at most {@code maxConcurrent} calls to one downstream system may be in flight at once,
 * whichever threads make them. A caller that can't get in within {@code maxWait} gets a
 * {@link BulkheadFullException} instead of joining an ever-longer line.
 *
 * <ul>
 *   <li>{@link #call} waits up to {@code maxWait} for a permit ({@code Duration.ZERO} means don't wait).</li>
 *   <li>No permit in time: throw {@code BulkheadFullException} with a message naming the bulkhead.</li>
 *   <li>Got a permit: run {@code work} and return its result, or let its exception propagate unchanged.</li>
 *   <li>Always give the permit back, whether {@code work} returned or threw.</li>
 * </ul>
 */
public final class Bulkhead {
    private final String name;
    private final Duration maxWait;
    private final Semaphore permits;

    public Bulkhead(String name, int maxConcurrent, Duration maxWait) {
        this.name = name;
        this.maxWait = maxWait;
        this.permits = new Semaphore(maxConcurrent);
    }

    public <T> T call(Callable<T> work) throws Exception {
        throw new UnsupportedOperationException("TODO: tryAcquire with maxWait, run work, release in finally");
    }

    /** Permits free right now. */
    public int available() {
        return permits.availablePermits();
    }

    public String name() {
        return name;
    }
}
