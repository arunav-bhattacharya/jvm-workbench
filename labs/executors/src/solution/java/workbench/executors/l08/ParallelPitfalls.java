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

    public static Map<String, Integer> stockLevels(List<String> products, StockLookup stock, ExecutorService io) {
        // 1. start every blocking lookup on the IO pool; none of them touches the common pool
        Map<String, CompletableFuture<Integer>> pending = products.stream()
                .distinct()
                .collect(Collectors.toMap(Function.identity(),
                        product -> CompletableFuture.supplyAsync(() -> stock.level(product), io)));
        // 2. wait here, on the caller's thread, which is allowed to block
        return pending.entrySet().stream()
                .collect(Collectors.toMap(Map.Entry::getKey, e -> e.getValue().join()));
    }
}
