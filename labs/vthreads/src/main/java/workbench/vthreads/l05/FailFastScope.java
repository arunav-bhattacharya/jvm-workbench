package workbench.vthreads.l05;

import java.util.concurrent.Callable;
import java.util.concurrent.ExecutionException;
import java.util.function.Supplier;

/**
 * A small "structured" scope built on JDK 21 APIs, so you can see what
 * {@code StructuredTaskScope} does for you. Use it like this:
 *
 * <pre>{@code
 * try (var scope = new FailFastScope()) {
 *     Supplier<Customer> customer = scope.fork(() -> crm.find(id));
 *     Supplier<Rate> rate = scope.fork(() -> fx.rate("EURUSD"));
 *     scope.join();                                  // throws if any subtask failed
 *     return new Quote(customer.get(), rate.get());
 * }                                                  // no subtask outlives this block
 * }</pre>
 *
 * <p>Rules:
 * <ul>
 *   <li>{@code fork} runs the task on a new virtual thread and returns a handle.</li>
 *   <li>The first subtask to fail cancels (interrupts) every other subtask at once: fail fast.
 *       A sibling that then fails because it was interrupted does not count as a failure.</li>
 *   <li>A subtask forked after the scope was cancelled never runs. Its handle's {@code get()}
 *       throws {@link IllegalStateException}.</li>
 *   <li>{@code join} waits until every subtask has finished, or until the first failure,
 *       whichever comes first. On a failure it throws {@link ExecutionException} with the
 *       first failure as its cause.</li>
 *   <li>A handle's {@code get()} returns the result only after {@code join}, and only for a
 *       subtask that succeeded. Otherwise it throws {@link IllegalStateException}.</li>
 *   <li>{@code close} cancels any subtask still running and waits until every forked thread
 *       has really ended, including its {@code finally} blocks.</li>
 * </ul>
 */
public final class FailFastScope implements AutoCloseable {

    public FailFastScope() {
        // TODO: you need a virtual-thread-per-task executor, a list of futures,
        //       a place for the first failure, and a "joined" flag (fields are fine)
    }

    /** Starts {@code task} on its own virtual thread. Its result is available after {@link #join()}. */
    public <T> Supplier<T> fork(Callable<T> task) {
        throw new UnsupportedOperationException("TODO: submit a wrapper that records the first failure and cancels the siblings");
    }

    /** Waits for every subtask, or for the first failure. Throws ExecutionException carrying that failure. */
    public void join() throws InterruptedException, ExecutionException {
        throw new UnsupportedOperationException("TODO: wait on each future; stop early once a failure is recorded");
    }

    /** Cancels whatever is still running and waits for every forked thread to end. */
    @Override
    public void close() {
        throw new UnsupportedOperationException("TODO: cancel what is still running, then wait for the threads");
    }
}
