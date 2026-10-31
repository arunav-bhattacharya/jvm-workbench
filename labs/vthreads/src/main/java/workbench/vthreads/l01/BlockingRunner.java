package workbench.vthreads.l01;

/**
 * Runs a blocking handler many times, the way a server runs one handler per request.
 *
 * <p>Both methods must return only after every task has finished, and return how
 * many tasks ran to the end.
 */
public final class BlockingRunner {
    private BlockingRunner() {}

    /**
     * Runs {@code handler} {@code tasks} times on a fixed pool of {@code poolSize} platform threads.
     * Use {@code Executors.newFixedThreadPool} in a try-with-resources block.
     */
    public static int runOnFixedPool(int poolSize, int tasks, Runnable handler) {
        throw new UnsupportedOperationException("TODO: submit every task to a fixed pool, wait for all, count completions");
    }

    /**
     * Runs {@code handler} {@code tasks} times, each time on its own new virtual thread.
     * Use {@code Executors.newVirtualThreadPerTaskExecutor} in a try-with-resources block.
     */
    public static int runOnVirtualThreads(int tasks, Runnable handler) {
        throw new UnsupportedOperationException("TODO: one virtual thread per task, wait for all, count completions");
    }
}
