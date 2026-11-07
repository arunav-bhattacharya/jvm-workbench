package workbench.executors.l08;

import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.function.Function;
import java.util.stream.Collectors;

public final class ParallelPitfalls {
    private ParallelPitfalls() {}

    public static List<String> flaggedIds(List<Payment> payments, long limitCents) {
        // no shared state: the stream builds the list itself, in encounter order
        return payments.parallelStream()
                .filter(p -> p.amountCents() > limitCents)
                .map(Payment::id)
                .toList();
    }

    public static Map<String, String> issuers(List<String> bins, BinLookup lookup, ExecutorService io) {
        // 1. start every blocking lookup on the IO pool; none of them touches the common pool
        Map<String, CompletableFuture<String>> pending = bins.stream()
                .distinct()
                .collect(Collectors.toMap(Function.identity(),
                        bin -> CompletableFuture.supplyAsync(() -> lookup.issuer(bin), io)));
        // 2. wait here, on the caller's thread, which is allowed to block
        return pending.entrySet().stream()
                .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().join()));
    }
}
