package workbench.executors.l09;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;

public final class BillJob {
    private final ExecutorService pool;
    private final OrderBook orders;

    public BillJob(ExecutorService pool, OrderBook orders) {
        this.pool = pool;
        this.orders = orders;
    }

    public List<String> run(List<String> tables) throws Exception {
        List<CompletableFuture<String>> bills = tables.stream()
                // 1. the blocking fetch runs on the pool
                .map(t -> CompletableFuture.supplyAsync(() -> orders.lines(t), pool)
                        // 2. render when the lines arrive: a callback, so no pool thread waits for anything
                        .thenApply(lines -> render(t, lines)))
                .toList();
        // 3. only the caller blocks, and it isn't a pool thread
        return bills.stream().map(CompletableFuture::join).toList();
    }

    static String render(String table, List<String> lines) {
        return table + ": " + lines.size() + " lines";
    }
}
