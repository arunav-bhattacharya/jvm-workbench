package workbench.executors.l05;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.ScheduledExecutorService;
import java.util.function.Supplier;

/**
 * Keeps an EUR/USD rate fresh for the checkout service.
 * <ul>
 *   <li>{@link #start()} fetches from {@code source} right away, then again {@code every} after the
 *       previous fetch finished (fixed delay, so a slow provider never causes back-to-back fetches).</li>
 *   <li>A fetch that throws keeps the last good rate and adds one to {@link #failures()}. It must not
 *       stop the schedule.</li>
 *   <li>{@link #close()} cancels the schedule. It does not shut down the scheduler, which belongs to the caller.</li>
 * </ul>
 * {@link #current()} is read by many request threads while the scheduler thread writes it.
 */
public final class FxRateRefresher implements AutoCloseable {
    private final ScheduledExecutorService scheduler;
    private final Supplier<BigDecimal> source;
    private final Duration every;

    public FxRateRefresher(ScheduledExecutorService scheduler, Supplier<BigDecimal> source, Duration every) {
        this.scheduler = scheduler;
        this.source = source;
        this.every = every;
    }

    public void start() {
        throw new UnsupportedOperationException("TODO: scheduleWithFixedDelay a SafeTask that stores the rate");
    }

    /** The last rate fetched successfully, or empty before the first success. */
    public Optional<BigDecimal> current() {
        throw new UnsupportedOperationException("TODO: return the last good rate");
    }

    public int failures() {
        throw new UnsupportedOperationException("TODO: count failed fetches");
    }

    @Override
    public void close() {
        throw new UnsupportedOperationException("TODO: cancel the scheduled future");
    }
}
