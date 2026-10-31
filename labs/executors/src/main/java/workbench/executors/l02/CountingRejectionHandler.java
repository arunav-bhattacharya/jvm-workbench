package workbench.executors.l02;

import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;

/**
 * A rejection handler for production: it counts every rejection (for a metric) and fails fast
 * with a message that says how full the pool was.
 *
 * <ul>
 *   <li>Every call adds one to {@link #rejected()}.</li>
 *   <li>If the pool is shut down, drop the task quietly: no exception.</li>
 *   <li>Otherwise throw {@link RejectedExecutionException} with exactly this message:
 *       {@code "rejected: pool=<pool size> active=<active count> queued=<queue size>"},
 *       for example {@code "rejected: pool=8 active=8 queued=16"}.</li>
 * </ul>
 */
public final class CountingRejectionHandler implements RejectedExecutionHandler {

    @Override
    public void rejectedExecution(Runnable task, ThreadPoolExecutor pool) {
        throw new UnsupportedOperationException("TODO: count, then drop (shut down) or throw with the pool's numbers");
    }

    /** How many tasks this handler has seen. */
    public long rejected() {
        throw new UnsupportedOperationException("TODO: return the count");
    }
}
