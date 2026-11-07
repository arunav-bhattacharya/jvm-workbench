package workbench.executors.l09;

import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadFactory;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

public final class ProductionPool extends ThreadPoolExecutor {
    private final FailureLog log;

    private ProductionPool(int threads, int queueCapacity, ThreadFactory factory, FailureLog log) {
        super(threads, threads, 0, TimeUnit.MILLISECONDS, new ArrayBlockingQueue<>(queueCapacity), factory);
        this.log = log;
    }

    public static ProductionPool create(String name, int threads, int queueCapacity, FailureLog log) {
        // JDK 21+: name-0, name-1, ... so thread dumps and log lines say which pool a thread belongs to
        ThreadFactory named = Thread.ofPlatform().name(name + "-", 0).factory();
        return new ProductionPool(threads, queueCapacity, named, log);
    }

    @Override
    public void execute(Runnable task) {
        // 1. capture on the submitting thread: this line runs before the task changes threads
        String requestId = RequestContext.get();
        super.execute(() -> {
            // 2. install it on the worker, remembering what the worker had
            String previous = RequestContext.get();
            RequestContext.set(requestId);
            try {
                task.run();
                // 3. submit() wrapped the task in a FutureTask, which keeps the exception to itself
                if (task instanceof Future<?> f && f.state() == Future.State.FAILED) {
                    log.failed(requestId, Thread.currentThread().getName(), f.exceptionNow());
                }
            } catch (RuntimeException | Error e) {
                // 4. execute(): the task threw; report it and keep this worker alive
                log.failed(requestId, Thread.currentThread().getName(), e);
            } finally {
                // 5. put the worker's own context back, so nothing leaks into the next task
                if (previous == null) RequestContext.clear();
                else RequestContext.set(previous);
            }
        });
    }
}
