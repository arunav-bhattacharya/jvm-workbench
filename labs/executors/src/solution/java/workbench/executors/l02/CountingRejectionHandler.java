package workbench.executors.l02;

import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.atomic.LongAdder;

public final class CountingRejectionHandler implements RejectedExecutionHandler {
    // many submitting threads can be rejected at once; LongAdder counts without contention
    private final LongAdder rejected = new LongAdder();

    @Override
    public void rejectedExecution(Runnable task, ThreadPoolExecutor pool) {
        rejected.increment();
        if (pool.isShutdown()) return;           // shutting down: dropping the task is expected
        // fail fast, and put the numbers an on-call engineer needs into the message
        throw new RejectedExecutionException("rejected: pool=" + pool.getPoolSize()
                + " active=" + pool.getActiveCount()
                + " queued=" + pool.getQueue().size());
    }

    public long rejected() {
        return rejected.sum();
    }
}
