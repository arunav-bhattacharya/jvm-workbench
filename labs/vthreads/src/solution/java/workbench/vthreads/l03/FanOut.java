package workbench.vthreads.l03;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public final class FanOut {
    private FanOut() {}

    public static <I, O> List<O> callAll(List<I> inputs, BlockingCall<I, O> call)
            throws InterruptedException, ExecutionException {
        // one new virtual thread per task; close() at the end of the block waits for all of them
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            // 1. fork: start every call before waiting for any
            List<Future<O>> futures = new ArrayList<>(inputs.size());
            for (I input : inputs) {
                futures.add(perTask.submit(() -> call.call(input)));
            }
            // 2. join: collect in input order; get() rethrows a failure as ExecutionException
            List<O> results = new ArrayList<>(inputs.size());
            for (Future<O> f : futures) {
                results.add(f.get());
            }
            return results;
        }
    }
}
