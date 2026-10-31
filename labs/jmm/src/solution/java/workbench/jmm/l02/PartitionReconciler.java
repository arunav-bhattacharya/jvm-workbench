package workbench.jmm.l02;

import java.util.ArrayList;
import java.util.List;
import java.util.function.LongSupplier;

public final class PartitionReconciler {
    private PartitionReconciler() {}

    public static long reconcile(List<LongSupplier> partitions) throws InterruptedException {
        long[] sums = new long[partitions.size()];
        List<Thread> workers = new ArrayList<>();
        for (int i = 0; i < partitions.size(); i++) {
            int slot = i;
            // hb: start() happens-before every action of the new thread, so it sees sums and partitions
            Thread worker = new Thread(() -> sums[slot] = partitions.get(slot).getAsLong());
            worker.start();
            workers.add(worker);
        }
        // hb: every action of a thread happens-before join() on it returns, so we see its write to sums
        for (Thread w : workers) w.join();
        long total = 0;
        for (long s : sums) total += s;
        return total;
    }
}
