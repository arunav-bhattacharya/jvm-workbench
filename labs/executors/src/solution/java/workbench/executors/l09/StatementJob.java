package workbench.executors.l09;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;

public final class StatementJob {
    private final ExecutorService pool;
    private final LedgerClient ledger;

    public StatementJob(ExecutorService pool, LedgerClient ledger) {
        this.pool = pool;
        this.ledger = ledger;
    }

    public List<String> run(List<String> merchants) throws Exception {
        List<CompletableFuture<String>> statements = merchants.stream()
                // 1. the blocking fetch runs on the pool
                .map(m -> CompletableFuture.supplyAsync(() -> ledger.lines(m), pool)
                        // 2. render when the lines arrive: a callback, so no pool thread waits for anything
                        .thenApply(lines -> render(m, lines)))
                .toList();
        // 3. only the caller blocks, and it isn't a pool thread
        return statements.stream().map(CompletableFuture::join).toList();
    }

    static String render(String merchant, List<String> lines) {
        return merchant + ": " + lines.size() + " lines";
    }
}
