package workbench.executors.l08;

import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.RecursiveTask;
import java.util.concurrent.atomic.LongAdder;

/** Fees over 2,000,000 ledger entries on a 4-worker ForkJoinPool. Args: [right|wrong] [threshold]. */
public class WorkStealingDemo {
    static final Map<String, LongAdder> LEAVES = new ConcurrentHashMap<>();

    static long fee(long amountCents) {
        long h = amountCents;
        for (int i = 0; i < 100; i++) h = (h * 31 + i) % 1_000_003;   // stands in for real fee rules
        return amountCents * 29 / 1_000 + 30 + h % 2;
    }

    static final class Fees extends RecursiveTask<Long> {
        final long[] amounts;
        final int from, to, threshold;
        final boolean wrong;

        Fees(long[] amounts, int from, int to, int threshold, boolean wrong) {
            this.amounts = amounts;
            this.from = from;
            this.to = to;
            this.threshold = threshold;
            this.wrong = wrong;
        }

        @Override
        protected Long compute() {
            if (to - from <= threshold) {
                LEAVES.computeIfAbsent(Thread.currentThread().getName(), k -> new LongAdder()).increment();
                long sum = 0;
                for (int i = from; i < to; i++) sum += fee(amounts[i]);
                return sum;
            }
            int mid = (from + to) >>> 1;
            Fees left = new Fees(amounts, from, mid, threshold, wrong);
            Fees right = new Fees(amounts, mid, to, threshold, wrong);
            left.fork();
            if (wrong) {
                long leftFees = left.join();           // waits for the left half before starting the right one
                return leftFees + right.compute();
            }
            long rightFees = right.compute();          // works on the right half while the left one can be stolen
            return left.join() + rightFees;
        }
    }

    public static void main(String[] args) {
        boolean wrong = args.length > 0 && args[0].equals("wrong");
        int threshold = args.length > 1 ? Integer.parseInt(args[1]) : 50_000;
        long[] amounts = new long[2_000_000];
        for (int i = 0; i < amounts.length; i++) amounts[i] = 100 + (i * 7919L) % 250_000;

        long s0 = System.nanoTime();
        long expected = 0;
        for (long a : amounts) expected += fee(a);                    // one thread, for comparison
        System.out.printf("one thread:  %,d ms%n", (System.nanoTime() - s0) / 1_000_000);

        try (ForkJoinPool pool = new ForkJoinPool(4)) {
            long t0 = System.nanoTime();
            long total = pool.submit(new Fees(amounts, 0, amounts.length, threshold, wrong)).join();
            long ms = (System.nanoTime() - t0) / 1_000_000;
            new TreeMap<>(LEAVES).forEach((thread, n) -> System.out.printf("%-24s %4d leaves%n", thread, n.sum()));
            System.out.printf("%s order, threshold %,d: %,d ms, %d steals, same total: %b%n",
                    wrong ? "wrong" : "right", threshold, ms, pool.getStealCount(), total == expected);
        }
    }
}
