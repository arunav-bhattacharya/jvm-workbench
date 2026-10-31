package workbench.executors.l02;

/**
 * Predict what a {@link java.util.concurrent.ThreadPoolExecutor} does with a burst of tasks,
 * without running it. The tests check your answer against a real pool.
 *
 * <p>Assume every task blocks until the test lets it go, so no thread ever becomes free
 * during the burst. Tasks are submitted one at a time with {@code execute}.
 */
public final class PoolMath {
    private PoolMath() {}

    /** Where the burst ended up: live threads, tasks waiting in the queue, tasks rejected. */
    public record Outcome(int threads, int queued, int rejected) {}

    /**
     * Apply the pool's rules to each of {@code tasks} submissions, in order.
     *
     * @param core          corePoolSize (at least 1)
     * @param max           maximumPoolSize (at least core)
     * @param queueCapacity how many tasks the queue can hold: 0 for a SynchronousQueue,
     *                      {@code Integer.MAX_VALUE} for an unbounded LinkedBlockingQueue
     * @param tasks         how many tasks arrive
     */
    public static Outcome predict(int core, int max, int queueCapacity, int tasks) {
        throw new UnsupportedOperationException("TODO: core threads, then the queue, then threads up to max, then reject");
    }
}
