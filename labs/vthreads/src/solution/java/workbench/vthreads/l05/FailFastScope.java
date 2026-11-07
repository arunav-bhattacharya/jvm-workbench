package workbench.vthreads.l05;

import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

public final class FailFastScope implements AutoCloseable {
    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
    private final List<Future<?>> futures = new CopyOnWriteArrayList<>();
    private final AtomicReference<Throwable> firstFailure = new AtomicReference<>();
    private volatile boolean joined;

    public FailFastScope() {}

    public <T> Supplier<T> fork(Callable<T> task) {
        Future<T> future;
        try {
            future = executor.submit(() -> {
                try {
                    return task.call();
                } catch (Throwable failure) {
                    // 1. only the first failure wins, and it cancels everyone else at once.
                    //    Siblings that then fail with InterruptedException lose the race and don't count.
                    if (firstFailure.compareAndSet(null, failure)) cancelAll();
                    throw failure;
                }
            });
        } catch (RejectedExecutionException scopeCancelled) {
            // 2. forked after the scope was cancelled: the task never runs
            return () -> {
                throw new IllegalStateException("subtask did not run: the scope was already cancelled");
            };
        }
        futures.add(future);
        return () -> {
            if (!joined) throw new IllegalStateException("call join() before get()");
            return future.resultNow();   // IllegalStateException if it failed or was cancelled
        };
    }

    public void join() throws InterruptedException, ExecutionException {
        for (Future<?> f : futures) {
            try {
                f.get();                 // an interrupted sibling finishes quickly with an exception
            } catch (CancellationException | ExecutionException e) {
                // the failure that matters is the first one, reported below
            }
            if (firstFailure.get() != null) break;   // 3. fail fast: don't wait for the rest
        }
        joined = true;
        Throwable failure = firstFailure.get();
        if (failure != null) throw new ExecutionException(failure);
    }

    @Override
    public void close() {
        cancelAll();                     // 4. interrupt anything still running
        executor.close();                // 5. wait until every forked thread has really ended
    }

    private void cancelAll() {
        // shutdownNow() interrupts every running subtask and rejects new forks. Unlike
        // Future.cancel(true), it does not mark the futures done early, so close() still
        // waits for each interrupted thread to finish its finally blocks.
        executor.shutdownNow();
    }
}
