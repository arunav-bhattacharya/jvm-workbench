package workbench.executors.l05;

import java.util.function.Consumer;

/**
 * Keeps a periodic task alive. A {@code ScheduledExecutorService} stops running a periodic task
 * forever, without a word, the first time one run throws. Wrap the task so that never happens.
 */
public final class SafeTask {
    private SafeTask() {}

    /**
     * Returns a Runnable that runs {@code task}. If {@code task} throws a {@code RuntimeException},
     * the wrapper passes it to {@code onError} and returns normally, so the next run still happens.
     * An {@code Error} is not caught.
     */
    public static Runnable wrap(Runnable task, Consumer<? super RuntimeException> onError) {
        throw new UnsupportedOperationException("TODO: try the task, report a RuntimeException, never rethrow it");
    }
}
