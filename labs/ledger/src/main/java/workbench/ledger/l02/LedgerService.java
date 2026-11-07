package workbench.ledger.l02;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.Future;
import java.util.concurrent.FutureTask;
import java.util.concurrent.RejectedExecutionHandler;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.atomic.AtomicLong;

/**
 * Runs the ledger on a bounded pool of platform threads named {@code ledger-0}, {@code ledger-1}, ...
 * Each task first appends the transfer to the journal (it may block), then applies it.
 *
 * <p>Every setting is a decision: core = max threads, a bounded {@code ArrayBlockingQueue}, a named
 * thread factory, and a rejection policy that counts and then throws, so the caller can answer
 * "busy, retry" and the dashboard shows how often that happens.
 */
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

    /**
     * Builds and starts the pool.
     *
     * <p>TODO: create a {@code CountingAbortPolicy}, then a {@code ThreadPoolExecutor} with
     * {@code plan.threads()} core and maximum threads, a keep-alive of 0, an
     * {@code ArrayBlockingQueue} of {@code plan.queueCapacity()}, the factory
     * {@code Thread.ofPlatform().name("ledger-", 0).factory()} and the policy. Call
     * {@code prestartAllCoreThreads()} and pass everything to the constructor.
     */
    public static LedgerService start(Ledger ledger, Journal journal, PoolPlan plan) {
        throw new UnsupportedOperationException("TODO: build the bounded, named pool with the counting policy");
    }

    /**
     * Queues a transfer and returns its future outcome. Throws {@code RejectedExecutionException}
     * when the queue is full or the service is shut down.
     *
     * <p>TODO: wrap the work in a {@link TransferTask} whose callable appends {@code t} to the
     * journal and then returns {@code ledger.apply(t)}. Hand it to {@code pool.execute} (not
     * {@code submit}, so the queue holds your TransferTask itself) and return it.
     */
    public Future<Outcome> submit(Transfer t) {
        throw new UnsupportedOperationException("TODO: TransferTask(journal, then apply), pool.execute, return it");
    }

    /**
     * Stops the service and accounts for every transfer: each one is applied, failed, or handed back.
     *
     * <p>TODO:
     * <ol>
     *   <li>{@code pool.shutdown()}: no new transfers, queued ones still run.</li>
     *   <li>Wait up to {@code grace} with {@code awaitTermination}. If the pool finished, return
     *       {@code new ShutdownReport(true, List.of())}.</li>
     *   <li>Otherwise call {@code shutdownNow()}. It interrupts running tasks and returns the queued
     *       ones. Cast each to {@code TransferTask}, {@code cancel(false)} it so a caller waiting in
     *       {@code get()} wakes up, and collect its transfer.</li>
     *   <li>Wait up to {@code grace} again for the interrupted tasks, then return
     *       {@code new ShutdownReport(false, neverStarted)}.</li>
     * </ol>
     */
    public ShutdownReport shutdown(Duration grace) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: shutdown, await, shutdownNow, cancel and hand back the queue");
    }

    /** How many transfers the pool turned away. */
    public long rejected() {
        return rejections.count();
    }

    public Ledger ledger() {
        return ledger;
    }

    /** What a shutdown did: whether the queue drained in time, and the transfers that never started. */
    public record ShutdownReport(boolean drained, List<Transfer> neverStarted) { }

    /** A FutureTask that remembers its transfer, so {@code shutdownNow()} hands back transfers you can log or replay. */
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

    /** Counts every rejection, then throws, like the default AbortPolicy. */
    static final class CountingAbortPolicy implements RejectedExecutionHandler {
        private final AtomicLong count = new AtomicLong();

        /**
         * TODO: increment {@code count}, then throw a {@code RejectedExecutionException} whose message
         * says how full the pool was: {@code pool.getActiveCount()}, {@code pool.getQueue().size()}
         * and {@code pool.isShutdown()}.
         */
        @Override
        public void rejectedExecution(Runnable task, ThreadPoolExecutor pool) {
            throw new UnsupportedOperationException("TODO: count it, then throw RejectedExecutionException");
        }

        long count() {
            return count.get();
        }
    }
}
