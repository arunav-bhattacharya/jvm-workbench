package workbench.executors.l02;

import java.util.concurrent.ThreadPoolExecutor;

/**
 * The pool that runs card authorizations. Build a {@link ThreadPoolExecutor} that meets this spec:
 * <ul>
 *   <li>4 core threads, and at most 8 threads in a burst.</li>
 *   <li>A bounded queue that holds 16 waiting tasks (an {@code ArrayBlockingQueue}).</li>
 *   <li>Threads above the core 4 retire after 30 seconds idle. Core threads never retire.</li>
 *   <li>The 4 core threads start right away, so the first burst doesn't wait for thread creation.</li>
 *   <li>When threads and queue are all full, {@code execute} throws {@code RejectedExecutionException}.</li>
 * </ul>
 */
public final class AuthPool {
    private AuthPool() {}

    public static ThreadPoolExecutor create() {
        throw new UnsupportedOperationException("TODO: new ThreadPoolExecutor(...) to the spec above");
    }
}
