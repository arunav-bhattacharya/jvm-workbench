package workbench.ledger.l02;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.Callable;
import java.util.concurrent.Future;
import java.util.concurrent.FutureTask;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

public final class LedgerService {
    private final Ledger ledger;
    private final Journal journal;
    private final ThreadPoolExecutor pool;
    private final CountingAbortPolicy rejections;

    private LedgerService(Ledger ledger, Journal journal, ThreadPoolExecutor pool, CountingAbortPolicy rejections) {
        this.ledger = ledger;
        this.journal = journal;
        this.pool = pool;
        this.rejections = rejections;
    }

    public static LedgerService start(Ledger ledger, Journal journal, PoolPlan plan) {
        CountingAbortPolicy rejections = new CountingAbortPolicy();
        ThreadPoolExecutor pool = new ThreadPoolExecutor(
                plan.threads(), plan.threads(),                    // core == max: extra threads would not help a full journal
                0, TimeUnit.MILLISECONDS,
                new ArrayBlockingQueue<>(plan.queueCapacity()),    // bounded: a full queue pushes back
                Thread.ofPlatform().name("ledger-", 0).factory(),  // ledger-0, ledger-1, ... in every dump and log line
                rejections);                                       // counted, then thrown at the caller
        pool.prestartAllCoreThreads();
        return new LedgerService(ledger, journal, pool, rejections);
    }

    public Future<Outcome> submit(Transfer t) {
        TransferTask task = new TransferTask(t, () -> {
            journal.append(t);              // 1. durable first; may block, holds no lock
            return ledger.apply(t);         // 2. then in memory, under the two account locks
        });
        pool.execute(task);                 // the queue holds this TransferTask, so shutdownNow() can hand it back
        return task;
    }

    public ShutdownReport shutdown(Duration grace) throws InterruptedException {
        pool.shutdown();                                                   // 1. no new transfers; the queue keeps draining
        if (pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS)) {
            return new ShutdownReport(true, List.of());                    // 2. everything accepted was applied
        }
        List<Transfer> neverStarted = new ArrayList<>();
        for (Runnable r : pool.shutdownNow()) {                            // 3. interrupt the running ones, take back the queue
            TransferTask task = (TransferTask) r;
            task.cancel(false);                                            //    a caller blocked in get() gets CancellationException
            neverStarted.add(task.transfer());
        }
        pool.awaitTermination(grace.toNanos(), TimeUnit.NANOSECONDS);      // 4. let the interrupted tasks finish
        return new ShutdownReport(false, List.copyOf(neverStarted));       //    and hand back what never ran
    }

    public long rejected() {
        return rejections.count();
    }

    public Ledger ledger() {
        return ledger;
    }

    public record ShutdownReport(boolean drained, List<Transfer> neverStarted) { }

    static final class TransferTask extends FutureTask<Outcome> {
        private final Transfer transfer;

        TransferTask(Transfer transfer, Callable<Outcome> work) {
            super(work);
            this.transfer = transfer;
        }

        Transfer transfer() {
            return transfer;
        }
    }

    static final class CountingAbortPolicy implements RejectedExecutionHandler {
        private final AtomicLong count = new AtomicLong();

        @Override
        public void rejectedExecution(Runnable task, ThreadPoolExecutor pool) {
            count.incrementAndGet();                         // every rejection is a "busy, retry" a client saw
            throw new RejectedExecutionException("ledger pool full: " + pool.getActiveCount() + " running, "
                    + pool.getQueue().size() + " queued" + (pool.isShutdown() ? ", shutting down" : ""));
        }

        long count() {
            return count.get();
        }
    }
}
