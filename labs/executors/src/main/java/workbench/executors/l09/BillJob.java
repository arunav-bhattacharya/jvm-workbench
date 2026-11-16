package workbench.executors.l09;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Future;

/**
 * At closing time, prints the day's bill for each table: fetch the table's order lines, then render them.
 *
 * <p>Bug: each table's task submits the fetch to the same pool and waits for it. When there are
 * at least as many tables as threads, every thread is a bill task waiting for a fetch that is
 * queued behind it, and the job hangs forever. Fix {@link #run} so it finishes on a pool of any
 * size, with no pool thread waiting for another task of the same pool. Keep the table order.
 */
public final class BillJob {
    private final ExecutorService pool;
    private final OrderBook orders;

    public BillJob(ExecutorService pool, OrderBook orders) {
        this.pool = pool;
        this.orders = orders;
    }

    /** Blocks the caller until every bill is ready. */
    public List<String> run(List<String> tables) throws Exception {
        List<Future<String>> bills = new ArrayList<>();
        for (String table : tables) {
            bills.add(pool.submit(() -> {
                Future<List<String>> lines = pool.submit(() -> orders.lines(table));   // a task inside a task, same pool
                return render(table, lines.get());                                     // waits for a task queued behind us
            }));
        }
        List<String> result = new ArrayList<>();
        for (Future<String> bill : bills) {
            result.add(bill.get());
        }
        return result;
    }

    static String render(String table, List<String> lines) {
        return table + ": " + lines.size() + " lines";
    }
}
