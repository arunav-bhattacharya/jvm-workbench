package workbench.concurrency.l01;

import java.util.List;

/**
 * Adds up a day's settled payment amounts, in cents, using several worker threads.
 *
 * <p>Write {@link #total}:
 * <ol>
 *   <li>Split the list into {@code workers} contiguous slices whose sizes differ by at most one.
 *       If there are fewer amounts than workers, start one thread per amount (none for an empty list).</li>
 *   <li>Start one new {@link Thread} per slice. Each thread adds up its own slice and stores the
 *       result in its own slot of a {@code long[]} array. No two threads write the same slot.</li>
 *   <li>Join every thread, then add up the slots on the calling thread and return the sum.</li>
 * </ol>
 * The calling thread must not read any amounts itself: all the adding happens on the workers.
 */
public final class LedgerTotals {
    private LedgerTotals() {}

    /**
     * Returns the sum of {@code amountsInCents}, computed by up to {@code workers} threads.
     *
     * @throws IllegalArgumentException if {@code workers} is less than 1
     */
    public static long total(List<Long> amountsInCents, int workers) throws InterruptedException {
        throw new UnsupportedOperationException("TODO: split into slices, start a thread per slice, join, combine");
    }
}
