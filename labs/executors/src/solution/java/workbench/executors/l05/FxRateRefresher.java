package workbench.executors.l05;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.Optional;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

public final class FxRateRefresher implements AutoCloseable {
    private final ScheduledExecutorService scheduler;
    private final Supplier<BigDecimal> source;
    private final Duration every;
    // written by the scheduler thread, read by request threads: AtomicReference makes the new rate visible
    private final AtomicReference<BigDecimal> rate = new AtomicReference<>();
    private final AtomicInteger failures = new AtomicInteger();
    private volatile ScheduledFuture<?> schedule;

    public FxRateRefresher(ScheduledExecutorService scheduler, Supplier<BigDecimal> source, Duration every) {
        this.scheduler = scheduler;
        this.source = source;
        this.every = every;
    }

    public void start() {
        Runnable refresh = SafeTask.wrap(
                () -> rate.set(source.get()),             // 1. fetch and publish
                e -> failures.incrementAndGet());         // 2. a failure keeps the old rate and the schedule
        schedule = scheduler.scheduleWithFixedDelay(      // 3. fixed delay: no catch-up bursts after a slow fetch
                refresh, 0, every.toMillis(), TimeUnit.MILLISECONDS);
    }

    public Optional<BigDecimal> current() {
        return Optional.ofNullable(rate.get());
    }

    public int failures() {
        return failures.get();
    }

    @Override
    public void close() {
        ScheduledFuture<?> s = schedule;
        if (s != null) s.cancel(false);                   // stop future runs; let a running fetch finish
    }
}
