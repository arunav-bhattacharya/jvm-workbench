package workbench.concurrency.l01;

import java.util.List;

public final class LedgerTotals {
    private LedgerTotals() {}

    public static long total(List<Long> amountsInCents, int workers) throws InterruptedException {
        if (workers < 1) throw new IllegalArgumentException("workers must be at least 1, was " + workers);
        int size = amountsInCents.size();
        int slices = Math.min(workers, size);          // never more threads than amounts
        long[] partial = new long[slices];             // one slot per worker: nothing is shared
        Thread[] threads = new Thread[slices];

        int base = slices == 0 ? 0 : size / slices;    // every slice gets this many
        int extra = slices == 0 ? 0 : size % slices;   // the first `extra` slices get one more
        int from = 0;
        for (int w = 0; w < slices; w++) {
            int start = from;
            int end = start + base + (w < extra ? 1 : 0);
            int slot = w;
            // 1. each worker reads only its own slice and writes only its own slot
            threads[w] = new Thread(() -> {
                long sum = 0;
                for (int i = start; i < end; i++) sum += amountsInCents.get(i);
                partial[slot] = sum;
            }, "ledger-worker-" + w);
            threads[w].start();                        // start(), not run(): run() would add on this thread
            from = end;
        }

        // 2. join makes each worker's write to its slot visible to this thread
        for (Thread t : threads) t.join();

        // 3. combine on the calling thread
        long total = 0;
        for (long p : partial) total += p;
        return total;
    }
}
