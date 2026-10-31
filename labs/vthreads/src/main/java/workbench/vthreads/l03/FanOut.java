package workbench.vthreads.l03;

import java.util.List;
import java.util.concurrent.ExecutionException;

/** Runs one blocking call per input, all at the same time, each on its own virtual thread. */
public final class FanOut {
    private FanOut() {}

    /**
     * Calls {@code call} once for every input, each on a new virtual thread, and returns the
     * results in the same order as the inputs. Returns only when every call has finished.
     *
     * <p>If a call throws, this method throws an {@link ExecutionException} whose cause is that
     * exception (what {@code Future.get()} gives you). This method does not limit concurrency:
     * that is the {@link Bulkhead}'s job.
     */
    public static <I, O> List<O> callAll(List<I> inputs, BlockingCall<I, O> call)
            throws InterruptedException, ExecutionException {
        throw new UnsupportedOperationException("TODO: newVirtualThreadPerTaskExecutor in try-with-resources, submit, then get in order");
    }
}
