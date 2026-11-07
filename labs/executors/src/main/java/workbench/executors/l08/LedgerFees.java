package workbench.executors.l08;

import java.util.concurrent.RecursiveTask;

/**
 * Totals the fees of a ledger with fork/join.
 *
 * <p>Write {@link #compute}. If the range {@code [from, to)} holds at most {@code threshold}
 * entries, add up the fees with a plain loop. Otherwise split it in two halves and run them in
 * parallel: fork one half, compute the other on this thread, then join the forked half.
 */
public class LedgerFees extends RecursiveTask<Long> {
    private final long[] amounts;
    private final FeeModel fees;
    private final int threshold;
    private final int from;
    private final int to;

    public LedgerFees(long[] amounts, FeeModel fees, int threshold) {
        this(amounts, fees, threshold, 0, amounts.length);
    }

    private LedgerFees(long[] amounts, FeeModel fees, int threshold, int from, int to) {
        if (threshold < 1) throw new IllegalArgumentException("threshold must be at least 1");
        this.amounts = amounts;
        this.fees = fees;
        this.threshold = threshold;
        this.from = from;
        this.to = to;
    }

    @Override
    protected Long compute() {
        throw new UnsupportedOperationException("TODO: small range? loop. Else split, fork one half, compute the other, join");
    }
}
