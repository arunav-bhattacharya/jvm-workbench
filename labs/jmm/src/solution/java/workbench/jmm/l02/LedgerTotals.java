package workbench.jmm.l02;

public class LedgerTotals {
    private long total;

    public synchronized void add(long cents) {
        total += cents;
    }

    // hb: the unlock at the end of add() happens-before the next lock of the same monitor (this) here,
    // so this read sees every add() that released the lock before we acquired it.
    public synchronized long total() {
        return total;
    }

    public long awaitAtLeast(long target) {
        long seen;
        while ((seen = total()) < target) {   // each call takes the lock, so each pass reads fresh
            Thread.onSpinWait();
        }
        return seen;
    }
}
