package workbench.vthreads.l01;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

public final class BlockingRunner {
    private BlockingRunner() {}

    public static int runOnFixedPool(int poolSize, int tasks, Runnable handler) {
        AtomicInteger done = new AtomicInteger();
        // poolSize OS threads; every other task waits in the pool's unbounded queue
        try (ExecutorService pool = Executors.newFixedThreadPool(poolSize)) {
            for (int i = 0; i < tasks; i++) {
                pool.execute(() -> {
                    handler.run();
                    done.incrementAndGet();
                });
            }
        } // close() = shutdown() + wait until every task has finished
        return done.get();
    }

    public static int runOnVirtualThreads(int tasks, Runnable handler) {
        AtomicInteger done = new AtomicInteger();
        // a brand-new virtual thread for every task, so nothing waits in a queue
        try (ExecutorService perTask = Executors.newVirtualThreadPerTaskExecutor()) {
            for (int i = 0; i < tasks; i++) {
                perTask.execute(() -> {
                    handler.run();
                    done.incrementAndGet();
                });
            }
        }
        return done.get();
    }
}
