package workbench.executors.l08;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.stream.Collectors;

/** Two parallel-stream bugs from a payment service. Fix both. */
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
     * The issuer of every BIN, looked up with {@code lookup}.
     *
     * <p>Bug: the lookups block, and a parallel stream runs them on the common ForkJoinPool,
     * which the whole JVM shares and which has only (cores - 1) threads. Run every lookup on
     * {@code io} instead, all at once, and wait for them here.
     */
    public static Map<String, String> issuers(List<String> bins, BinLookup lookup, ExecutorService io) {
        return bins.parallelStream()
                .collect(Collectors.toMap(bin -> bin, lookup::issuer));   // blocking calls in the common pool
    }
}
