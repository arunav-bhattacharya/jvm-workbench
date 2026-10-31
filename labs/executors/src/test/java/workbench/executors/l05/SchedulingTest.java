package workbench.executors.l05;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.BooleanSupplier;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatCode;
import static workbench.executors.l05.Schedules.Mode.FIXED_DELAY;
import static workbench.executors.l05.Schedules.Mode.FIXED_RATE;

class SchedulingTest {
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
        Thread t = new Thread(r, "test-scheduler");
        t.setDaemon(true);
        return t;
    });

    @AfterEach
    void stop() {
        scheduler.shutdownNow();
    }

    private static boolean eventually(BooleanSupplier condition) throws InterruptedException {
        long deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(10);
        while (System.nanoTime() < deadline) {
            if (condition.getAsBoolean()) return true;
            Thread.sleep(5);
        }
        return condition.getAsBoolean();
    }

    @Test
    @DisplayName("fixed rate: short runs start exactly on the timetable")
    void fixedRateOnTime() {
        assertThat(Schedules.startTimes(FIXED_RATE, 0, 100, new long[] {10, 10, 10, 10}))
                .containsExactly(0, 100, 200, 300);
        assertThat(Schedules.startTimes(FIXED_RATE, 50, 100, new long[] {10, 10, 10}))
                .containsExactly(50, 150, 250);
    }

    @Test
    @DisplayName("fixed rate: after a slow run, late runs start back to back until they catch up")
    void fixedRateCatchesUp() {
        // run 1 takes 250 ms: runs 2 and 3 are overdue, so they start as soon as the previous one ends
        assertThat(Schedules.startTimes(FIXED_RATE, 0, 100, new long[] {10, 250, 10, 10, 10}))
                .containsExactly(0, 100, 350, 360, 400);
    }

    @Test
    @DisplayName("fixed delay: each run starts a full delay after the previous one ends")
    void fixedDelay() {
        assertThat(Schedules.startTimes(FIXED_DELAY, 0, 100, new long[] {10, 250, 10, 10}))
                .containsExactly(0, 110, 460, 570);
        assertThat(Schedules.startTimes(FIXED_DELAY, 20, 100, new long[0])).isEmpty();
    }

    @Test
    @DisplayName("SafeTask reports a RuntimeException instead of letting it escape")
    void safeTaskCatches() {
        List<RuntimeException> errors = new ArrayList<>();
        IllegalStateException boom = new IllegalStateException("health check failed");
        Runnable safe = SafeTask.wrap(() -> { throw boom; }, errors::add);
        assertThatCode(safe::run).doesNotThrowAnyException();
        assertThat(errors).containsExactly(boom);

        AtomicInteger runs = new AtomicInteger();
        SafeTask.wrap(runs::incrementAndGet, errors::add).run();
        assertThat(runs.get()).isEqualTo(1);
        assertThat(errors).hasSize(1);
    }

    @Test
    @DisplayName("SafeTask keeps a fixed-rate schedule alive after runs 2 and 4 throw")
    void safeTaskKeepsScheduleAlive() throws Exception {
        AtomicInteger runs = new AtomicInteger();
        AtomicInteger errors = new AtomicInteger();
        CountDownLatch sixRuns = new CountDownLatch(6);
        Runnable check = () -> {
            int n = runs.incrementAndGet();
            sixRuns.countDown();
            if (n == 2 || n == 4) throw new IllegalStateException("ledger unreachable on run " + n);
        };
        scheduler.scheduleAtFixedRate(SafeTask.wrap(check, e -> errors.incrementAndGet()), 0, 10, TimeUnit.MILLISECONDS);
        assertThat(sixRuns.await(10, TimeUnit.SECONDS)).as("reached 6 runs").isTrue();
        assertThat(errors.get()).isEqualTo(2);
    }

    @Test
    @DisplayName("FxRateRefresher publishes the first rate right after start()")
    void refresherFetchesAtOnce() throws Exception {
        try (FxRateRefresher fx = new FxRateRefresher(scheduler, () -> new BigDecimal("1.0842"), Duration.ofMillis(20))) {
            fx.start();
            assertThat(eventually(() -> fx.current().isPresent())).as("a rate arrived").isTrue();
            assertThat(fx.current()).contains(new BigDecimal("1.0842"));
        }
    }

    @Test
    @DisplayName("FxRateRefresher keeps the last good rate through failures, and keeps refreshing")
    void refresherSurvivesFailures() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        try (FxRateRefresher fx = new FxRateRefresher(scheduler, () -> {
            int n = calls.incrementAndGet();
            if (n == 1) return new BigDecimal("1.0800");
            if (n <= 3) throw new IllegalStateException("provider timeout");
            return new BigDecimal("1.0900");
        }, Duration.ofMillis(10))) {
            fx.start();
            assertThat(eventually(() -> fx.current().isPresent())).isTrue();
            assertThat(eventually(() -> fx.current().get().equals(new BigDecimal("1.0900"))))
                    .as("rate after the provider recovered").isTrue();
            assertThat(fx.failures()).isEqualTo(2);
        }
    }

    @Test
    @DisplayName("FxRateRefresher.close() stops the refreshes")
    void refresherStops() throws Exception {
        AtomicInteger calls = new AtomicInteger();
        FxRateRefresher fx = new FxRateRefresher(scheduler, () -> {
            calls.incrementAndGet();
            return BigDecimal.ONE;
        }, Duration.ofMillis(5));
        fx.start();
        assertThat(eventually(() -> calls.get() >= 3)).isTrue();
        fx.close();
        int atClose = calls.get();
        Thread.sleep(200);
        assertThat(calls.get()).as("calls after close").isLessThanOrEqualTo(atClose + 1);
        assertThat(scheduler.isShutdown()).as("close() must not shut down the caller's scheduler").isFalse();
    }
}
