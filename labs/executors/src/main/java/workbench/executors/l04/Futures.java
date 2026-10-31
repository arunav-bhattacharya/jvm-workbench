package workbench.executors.l04;

import java.time.Duration;
import java.util.concurrent.Future;

/** Two small helpers every service that calls slow dependencies ends up writing. */
public final class Futures {
    private Futures() {}

    /**
     * Waits up to {@code timeout} for {@code future}'s result.
     * <ul>
     *   <li>Done in time: return the result.</li>
     *   <li>Timed out: cancel the task with an interrupt ({@code cancel(true)}) and return {@code fallback}.</li>
     *   <li>The task failed or was cancelled: return {@code fallback}.</li>
     *   <li>The calling thread is interrupted while waiting: cancel the task with an interrupt and
     *       let the {@link InterruptedException} propagate.</li>
     * </ul>
     */
    public static <T> T getOrDefault(Future<T> future, Duration timeout, T fallback) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: get with a timeout, cancel on timeout, fall back on failure");
    }

    /**
     * A one-line status for logs, using {@code Future.state()} (JDK 19+):
     * {@code "running"}, {@code "success: <result>"}, {@code "failed: <exception message>"} or {@code "cancelled"}.
     * Must never block.
     */
    public static String describe(Future<?> future) {
        throw new UnsupportedOperationException("TODO: switch on future.state(), use resultNow() and exceptionNow()");
    }
}
