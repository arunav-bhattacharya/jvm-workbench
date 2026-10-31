package workbench.jmm.l02;

/**
 * A running total of ledger postings. Many posting threads call {@link #add}. A report thread
 * calls {@link #awaitAtLeast} to wait until the day's postings are in.
 *
 * <p>The bug: {@link #total()} reads the field with no happens-before edge to the writes in
 * {@code add}, so a waiting reader may never see the total move. Fix it, then write a
 * {@code // hb:} comment that names the edge your fix relies on.
 */
public class LedgerTotals {
    private long total;   // cents

    public synchronized void add(long cents) {
        total += cents;
    }

    public long total() {
        return total;
    }

    /** Spins until the total reaches {@code target}, then returns the total it saw. */
    public long awaitAtLeast(long target) {
        long seen;
        while ((seen = total()) < target) {
            // wait for the posting threads
        }
        return seen;
    }
}
