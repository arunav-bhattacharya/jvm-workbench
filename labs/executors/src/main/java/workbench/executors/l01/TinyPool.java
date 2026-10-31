package workbench.executors.l01;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executor;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

/**
 * A fixed-size thread pool you can read in one sitting: N worker threads that loop,
 * taking tasks from one shared queue and running them.
 *
 * <p>The constructor, {@link #isShutdown()}, {@link #isTerminated()}, {@link #failedTasks()}
 * and {@link #close()} are done. You write the five methods marked TODO:
 * <ul>
 *   <li>{@link #execute}: queue the task, or reject it once the pool is shut down.</li>
 *   <li>{@code workerLoop}: what every worker thread runs, over and over.</li>
 *   <li>{@link #shutdown}: stop taking new tasks, let queued ones finish, return at once.</li>
 *   <li>{@link #shutdownNow}: stop taking new tasks, interrupt running ones, hand back the rest.</li>
 *   <li>{@link #awaitTermination}: wait until every worker has exited.</li>
 * </ul>
 */
public final class TinyPool implements Executor, AutoCloseable {
    /** A marker task. A worker that takes it from the queue exits. One per worker on shutdown. */
    private static final Runnable POISON = () -> { };

    private final BlockingQueue<Runnable> queue = new LinkedBlockingQueue<>();
    private final List<Thread> workers = new ArrayList<>();
    private final CountDownLatch terminated;            // each worker counts down once, when it exits
    private final AtomicLong failed = new AtomicLong();
    private final Object lock = new Object();           // guards 'shutdown' and every queue.add
    private boolean shutdown;                           // guarded by lock

    /** Starts {@code threads} workers named {@code namePrefix + 0}, {@code namePrefix + 1}, and so on. */
    public TinyPool(int threads, String namePrefix) {
        if (threads < 1) throw new IllegalArgumentException("threads must be at least 1");
        terminated = new CountDownLatch(threads);
        for (int i = 0; i < threads; i++) {
            workers.add(new Thread(this::runWorker, namePrefix + i));
        }
        workers.forEach(Thread::start);
    }

    private void runWorker() {
        try {
            workerLoop();
        } finally {
            terminated.countDown();                     // this worker is gone
        }
    }

    /**
     * Runs on every worker thread until the worker should exit.
     *
     * <p>Take a task from {@code queue} (blocking while it is empty) and run it. Repeat.
     * <ul>
     *   <li>If the task is {@link #POISON}, return: the pool is shutting down.</li>
     *   <li>If {@code take()} is interrupted, return: {@link #shutdownNow} is stopping the pool.</li>
     *   <li>If the task throws a {@code RuntimeException}, count it in {@code failed} and keep going.
     *       One bad task must not kill a worker.</li>
     * </ul>
     */
    private void workerLoop() {
        throw new UnsupportedOperationException("TODO: take tasks from the queue and run them until shut down");
    }

    /**
     * Queues {@code task} to run on some worker, some time later.
     *
     * @throws NullPointerException if {@code task} is null
     * @throws RejectedExecutionException if {@link #shutdown} or {@link #shutdownNow} was called
     */
    @Override
    public void execute(Runnable task) {
        throw new UnsupportedOperationException("TODO: reject if shut down, otherwise queue the task");
    }

    /**
     * Stops accepting new tasks. Tasks already queued still run. Returns at once: it does not wait.
     * Calling it twice is harmless.
     */
    public void shutdown() {
        throw new UnsupportedOperationException("TODO: mark the pool shut down and wake every worker");
    }

    /**
     * Stops accepting new tasks, removes the tasks that never started, interrupts the workers,
     * and returns the removed tasks in queue order.
     */
    public List<Runnable> shutdownNow() {
        throw new UnsupportedOperationException("TODO: drain the queue, interrupt the workers");
    }

    /** Waits until every worker has exited, or the timeout passes. Returns true if they all exited. */
    public boolean awaitTermination(long timeout, TimeUnit unit) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: wait on the terminated latch");
    }

    public boolean isShutdown() {
        synchronized (lock) {
            return shutdown;
        }
    }

    public boolean isTerminated() {
        return terminated.getCount() == 0;
    }

    /** How many tasks have thrown so far. */
    public long failedTasks() {
        return failed.get();
    }

    /**
     * Shuts down and waits for every queued task to finish. If the waiting thread is interrupted,
     * it switches to {@link #shutdownNow()}, keeps waiting, and restores the interrupt flag at the end.
     * This is the same contract as {@code ExecutorService.close()} (JDK 19 and later).
     */
    @Override
    public void close() {
        shutdown();
        boolean interrupted = false;
        while (true) {
            try {
                if (awaitTermination(1, TimeUnit.DAYS)) break;
            } catch (InterruptedException e) {
                if (!interrupted) {
                    shutdownNow();
                    interrupted = true;
                }
            }
        }
        if (interrupted) Thread.currentThread().interrupt();
    }
}
