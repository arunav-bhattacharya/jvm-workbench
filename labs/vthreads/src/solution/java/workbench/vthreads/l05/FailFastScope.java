package workbench.vthreads.l05;

import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;

public final class FailFastScope implements AutoCloseable {
    private final ExecutorService executor = Executors.newVirtualThreadPerTaskExecutor();
    private final List<Future<?>> futures = new CopyOnWriteArrayList<>();   // failing subtasks iterate it
    private final AtomicReference<Throwable> firstFailure = new AtomicReference<>();
    private volatile boolean joined;
    private volatile boolean cancelled;   // set once the scope starts cancelling

    public FailFastScope() {}

    public <T> Supplier<T> fork(Callable<T> task) {
        Future<T> future = executor.submit(() -> {
            try {
                return task.call();
            } catch (Throwable failure) {
                // 1. only the first real failure wins, and it cancels everyone else right away;
                //    a subtask that fails because we cancelled it doesn't count
                if (!cancelled && firstFailure.compareAndSet(null, failure)) cancelAll();
                throw failure;
            }
        });
        futures.add(future);
        // 2. forked after a failure: don't let it run on
        if (cancelled) future.cancel(true);
        return () -> {
            if (!joined) throw new IllegalStateException("call join() before get()");
            return future.resultNow();   // IllegalStateException if it failed or was cancelled
        };
    }

    public void join() throws InterruptedException, ExecutionException {
        for (Future<?> f : futures) {
            try {
                f.get();                 // a cancelled sibling returns at once with CancellationException
            } catch (CancellationException | ExecutionException e) {
                // reported below as the first failure
            }
            if (firstFailure.get() != null) break;   // 3. fail fast: don't wait for slow siblings
        }
        joined = true;
        Throwable failure = firstFailure.get();
        if (failure != null) throw new ExecutionException(failure);
    }

    @Override
    public void close() {
        cancelAll();                     // 4. interrupt anything still running (no-op for finished tasks)
        executor.close();                // 5. wait until every forked thread has ended
    }

    private void cancelAll() {
        cancelled = true;
        for (Future<?> f : futures) f.cancel(true);
    }
}
