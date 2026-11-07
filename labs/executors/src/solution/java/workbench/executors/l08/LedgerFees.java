package workbench.executors.l08;

import java.util.concurrent.RecursiveTask;

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
        // 1. small enough: a plain loop beats any more splitting
        if (to - from <= threshold) {
            long sum = 0;
            for (int i = from; i < to; i++) {
                sum += fees.feeCents(amounts[i]);
            }
            return sum;
        }
        // 2. split in two
        int mid = (from + to) >>> 1;
        LedgerFees left = new LedgerFees(amounts, fees, threshold, from, mid);
        LedgerFees right = new LedgerFees(amounts, fees, threshold, mid, to);
        // 3. fork the left half: it goes on this worker's deque, where an idle worker can steal it
        return left.compute() + right.compute();
    }
}
