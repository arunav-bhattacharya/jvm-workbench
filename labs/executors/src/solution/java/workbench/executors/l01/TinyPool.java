package workbench.executors.l01;

import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executor;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

public final class TinyPool implements Executor, AutoCloseable {
    private static final Runnable POISON = () -> { };

    private final BlockingQueue<Runnable> queue = new LinkedBlockingQueue<>();
    private final List<Thread> workers = new ArrayList<>();
    private final CountDownLatch terminated;
    private final AtomicLong failed = new AtomicLong();
    private final Object lock = new Object();
    private boolean shutdown;

    public TinyPool(int threads, String namePrefix) {
        if (threads < 1) throw new IllegalArgumentException("threads must be at least 1");
        terminated = new CountDownLatch(threads);
        for (int i = 0; i < threads; i++) {
            workers.add(new Thread(this::runWorker, namePrefix + i));
        }
        workers.forEach(Thread::start);
    }

    private void runWorker() {
        try {
            workerLoop();
        } finally {
            terminated.countDown();
        }
    }

    private void workerLoop() {
        while (true) {
            Runnable task;
            try {
                task = queue.take();                  // 1. sleep until there is work
            } catch (InterruptedException e) {
                return;                               // shutdownNow() interrupted an idle worker
            }
            if (task == POISON) return;               // 2. shutdown(): every real task before the pill has run
            try {
                task.run();                           // 3. run it on this thread
            } catch (RuntimeException e) {
                failed.incrementAndGet();             // 4. count it and keep the worker alive
            }
            // ThreadPoolExecutor also clears an interrupt flag a task leaves behind. TinyPool skips that,
            // so a task that leaves the flag set makes the next take() throw and the worker exit.
        }
    }

    @Override
    public void execute(Runnable task) {
        Objects.requireNonNull(task, "task");
        // check and queue under one lock, so a task can never slip in behind the poison pills
        synchronized (lock) {
            if (shutdown) throw new RejectedExecutionException("TinyPool is shut down");
            queue.add(task);
        }
    }

    public void shutdown() {
        synchronized (lock) {
            if (shutdown) return;
            shutdown = true;
            // one pill per worker, queued behind every real task: workers finish the backlog, then exit
            for (int i = 0; i < workers.size(); i++) queue.add(POISON);
        }
        // no waiting here: that is awaitTermination's job
    }

    public List<Runnable> shutdownNow() {
        List<Runnable> neverStarted = new ArrayList<>();
        synchronized (lock) {
            shutdown = true;
            queue.drainTo(neverStarted);              // take out everything that has not started
            neverStarted.removeIf(t -> t == POISON);  // pills from an earlier shutdown() are not tasks
            for (int i = 0; i < workers.size(); i++) queue.add(POISON);  // wake workers whose task ignores interrupts
        }
        workers.forEach(Thread::interrupt);           // ask running tasks to stop; idle workers exit from take()
        return neverStarted;
    }

    public boolean awaitTermination(long timeout, TimeUnit unit) throws InterruptedException {
        return terminated.await(timeout, unit);
    }

    public boolean isShutdown() {
        synchronized (lock) {
            return shutdown;
        }
    }

    public boolean isTerminated() {
        return terminated.getCount() == 0;
    }

    public long failedTasks() {
        return failed.get();
    }

    @Override
    public void close() {
        shutdown();
        boolean interrupted = false;
        while (true) {
            try {
                if (awaitTermination(1, TimeUnit.DAYS)) break;
            } catch (InterruptedException e) {
                if (!interrupted) {
                    shutdownNow();
                    interrupted = true;
                }
            }
        }
        if (interrupted) Thread.currentThread().interrupt();
    }
}
