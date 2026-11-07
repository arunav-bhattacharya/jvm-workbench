package workbench.concurrency.l09;

import java.time.Duration;
import java.util.List;

/**
 * Collects ledger entries from many request threads and hands them to one writer thread in
 * batches, so the writer can insert 100 rows per round trip instead of one.
 *
 * <ul>
 *   <li>Back it with a bounded {@link java.util.concurrent.BlockingQueue} of {@code capacity}.</li>
 *   <li>{@link #submit} never blocks: it returns false when the queue is full (the caller answers "retry later").</li>
 *   <li>{@link #nextBatch} waits up to {@code maxWait} for the first entry. Then it takes whatever else is
 *       already queued, without waiting, up to {@code max} entries in total, oldest first.
 *       It returns an empty list if nothing arrived in time.</li>
 * </ul>
 */
public class Batcher<T> {

    /** @throws IllegalArgumentException if {@code capacity} is less than 1 */
    public Batcher(int capacity) {
        throw new UnsupportedOperationException("TODO: create a bounded BlockingQueue");
    }

    /** Queues {@code entry} if there is room. Returns false at once if the queue is full. */
    public boolean submit(T entry) {
        throw new UnsupportedOperationException("TODO: offer, not put");
    }

    /** Up to {@code max} entries, oldest first; waits up to {@code maxWait} for the first one. */
    public List<T> nextBatch(int max, Duration maxWait) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: poll with a timeout for the first entry, then drainTo for the rest");
    }

    /** How many entries are waiting. */
    public int pending() {
        throw new UnsupportedOperationException("TODO");
    }
}
