package workbench.concurrency.l10;

import java.time.Duration;
import java.util.concurrent.Callable;
import java.util.concurrent.Semaphore;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/**
 * Limits how many calls to the card-issuer API run at once. The issuer allows 4 concurrent
 * calls per client; a fifth gets throttled.
 *
 * <p>This version has the two classic permit bugs. Both hand out permits that were never taken,
 * so under load more than {@code maxConcurrent} calls run at once:
 * <ol>
 *   <li>{@link #call(Callable)} acquires inside the {@code try}. If the wait is interrupted,
 *       the {@code finally} still releases a permit this thread never had.</li>
 *   <li>{@link #call(Callable, Duration)} ignores the result of {@code tryAcquire}, so it runs the
 *       task (and releases) even when no permit was free.</li>
 * </ol>
 * Fix both. The timed version must throw {@link TimeoutException} without running the task.
 */
public class IssuerGate {
    private final Semaphore permits;

    public IssuerGate(int maxConcurrent) {
        this.permits = new Semaphore(maxConcurrent);
    }

    /** Runs {@code task} while holding a permit, waiting as long as it takes for one. */
    public <T> T call(Callable<T> task) throws Exception {
        try {
            permits.acquire();               // inside the try: an interrupted wait still reaches finally
            return task.call();
        } finally {
            permits.release();
        }
    }

    /** Runs {@code task} while holding a permit; throws TimeoutException if none is free within {@code maxWait}. */
    public <T> T call(Callable<T> task, Duration maxWait) throws Exception {
        permits.tryAcquire(maxWait.toNanos(), TimeUnit.NANOSECONDS);   // the answer is thrown away
        try {
            return task.call();
        } finally {
            permits.release();
        }
    }

    /** Permits free right now. */
    public int available() {
        return permits.availablePermits();
    }
}
