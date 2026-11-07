package workbench.executors.l09;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * A fixed-size pool fit for production.
 *
 * <ul>
 *   <li>{@link #create}: threads are named {@code name-0}, {@code name-1}, ... and the queue is
 *       bounded, so a burst is rejected instead of piling up.</li>
 *   <li>{@link #execute}: every task runs with the {@link RequestContext} of the thread that
 *       submitted it, and the worker's own context is put back afterwards, so nothing leaks into
 *       the next task on that thread.</li>
 *   <li>{@link #execute}: a task that fails is reported once to the {@link FailureLog}, with the
 *       submitter's request id, the worker's name and the original exception. That covers
 *       {@code execute} (the task throws) and {@code submit} (the exception is inside the
 *       {@code Future}). Don't rethrow: the worker thread stays alive for the next task.</li>
 * </ul>
 * {@code submit}, {@code invokeAll} and {@code CompletableFuture.supplyAsync(task, pool)} all end
 * up in {@code execute}, so it is the one place to wrap.
 */
public final class ProductionPool extends ThreadPoolExecutor {
    private final FailureLog log;

    private ProductionPool(int threads, int queueCapacity, ThreadFactory factory, FailureLog log) {
        super(threads, threads, 0, TimeUnit.MILLISECONDS, new ArrayBlockingQueue<>(queueCapacity), factory);
        this.log = log;
    }

    public static ProductionPool create(String name, int threads, int queueCapacity, FailureLog log) {
        throw new UnsupportedOperationException("TODO: name the threads with Thread.ofPlatform().name(name + \"-\", 0).factory()");
    }

    @Override
    public void execute(Runnable task) {
        throw new UnsupportedOperationException("TODO: capture the request id here, wrap the task, then super.execute(wrapper)");
    }
}
