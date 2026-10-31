package workbench.jmm.l02;

import java.util.List;
import java.util.function.LongSupplier;

/**
 * Sums each partition of a reconciliation run on its own thread and adds up the results.
 *
 * <p>The bug: the caller sleeps and hopes the workers are done. Sleeping is neither a wait
 * for completion nor a happens-before edge. Fix it so the total always includes every
 * partition, then write {@code // hb:} comments for the two edges you rely on.
 */
public final class PartitionReconciler {
    private PartitionReconciler() {}

    /** Returns the sum of every partition's value, computing each partition on its own thread. */
    public static long reconcile(List<LongSupplier> partitions) throws InterruptedException {
        long[] sums = new long[partitions.size()];
        for (int i = 0; i < partitions.size(); i++) {
            int slot = i;
            Thread worker = new Thread(() -> sums[slot] = partitions.get(slot).getAsLong());
            worker.start();
        }
        Thread.sleep(50);   // "plenty of time for the workers"
        long total = 0;
        for (long s : sums) total += s;
        return total;
    }
}
