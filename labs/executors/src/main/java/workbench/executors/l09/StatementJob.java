package workbench.executors.l09;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;

/**
 * Builds the month-end statement for each merchant: fetch its ledger lines, then render them.
 *
 * <p>Bug: each merchant's task submits the fetch to the same pool and waits for it. When there are
 * at least as many merchants as threads, every thread is a statement task waiting for a fetch that
 * is queued behind it, and the job hangs forever. Fix {@link #run} so it finishes on a pool of any
 * size, with no pool thread waiting for another task of the same pool. Keep the merchant order.
 */
public final class StatementJob {
    private final ExecutorService pool;
    private final LedgerClient ledger;

    public StatementJob(ExecutorService pool, LedgerClient ledger) {
        this.pool = pool;
        this.ledger = ledger;
    }

    /** Blocks the caller until every statement is ready. */
    public List<String> run(List<String> merchants) throws Exception {
        List<Future<String>> statements = new ArrayList<>();
        for (String merchant : merchants) {
            statements.add(pool.submit(() -> {
                Future<List<String>> lines = pool.submit(() -> ledger.lines(merchant));   // a task inside a task, same pool
                return render(merchant, lines.get());                                     // waits for a task queued behind us
            }));
        }
        List<String> result = new ArrayList<>();
        for (Future<String> statement : statements) {
            result.add(statement.get());
        }
        return result;
    }

    static String render(String merchant, List<String> lines) {
        return merchant + ": " + lines.size() + " lines";
    }
}
