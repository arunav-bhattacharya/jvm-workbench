package workbench.executors.l08;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.stream.Collectors;

/** Two parallel-stream bugs from the restaurant's back office. Fix both. */
public final class ParallelPitfalls {
    private ParallelPitfalls() {}

    /**
     * Ids of the payments above {@code limitCents}, in the same order as {@code payments}.
     *
     * <p>Bug: the parallel stream adds to a shared {@code ArrayList}. It loses ids, scrambles
     * their order and sometimes throws. Keep the parallel stream; remove the shared state.
     */
    public static List<String> flaggedIds(List<Payment> payments, long limitCents) {
        List<String> flagged = new ArrayList<>();
        payments.parallelStream()
                .filter(p -> p.amountCents() > limitCents)
                .forEach(p -> flagged.add(p.id()));       // many threads, one ArrayList
        return flagged;
    }

    /**
     * How many of each product are left, asked from the stock service with {@code stock}.
     *
     * <p>Bug: the lookups block, and a parallel stream runs them on the common ForkJoinPool,
     * which the whole JVM shares and which has only (cores - 1) threads. Run every lookup on
     * {@code io} instead, all at once, and wait for them here.
     */
    public static Map<String, Integer> stockLevels(List<String> products, StockLookup stock, ExecutorService io) {
        return products.parallelStream()
                .collect(Collectors.toMap(product -> product, stock::level));   // blocking calls in the common pool
    }
}
