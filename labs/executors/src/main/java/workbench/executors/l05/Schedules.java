package workbench.executors.l05;

/**
 * A model of when a periodic task starts, in virtual milliseconds, so you can reason about
 * fixed rate and fixed delay without a clock. Assume one task on one scheduler thread.
 */
public final class Schedules {
    private Schedules() {}

    public enum Mode { FIXED_RATE, FIXED_DELAY }

    /**
     * Returns the start time of each run. Run {@code n} takes {@code durations[n]} ms.
     * <ul>
     *   <li>The first run starts at {@code initialDelay}.</li>
     *   <li>FIXED_RATE: run {@code n} is due at {@code initialDelay + n * period}. It starts when it is
     *       due, or when run {@code n - 1} ends if that is later. Runs never overlap.</li>
     *   <li>FIXED_DELAY: run {@code n} starts {@code period} ms after run {@code n - 1} ends.</li>
     * </ul>
     */
    public static long[] startTimes(Mode mode, long initialDelay, long period, long[] durations) {
        throw new UnsupportedOperationException("TODO: compute each start from the previous run's end");
    }
}
