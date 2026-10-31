// Java equivalent of FailureSpreads.kt with a virtual-thread executor (JDK 21+, no preview APIs).
// An executor has no parent-child tree: a failed task does not cancel its sibling unless you do it.
// Pass "cancel" to cancel the sibling by hand, which is what coroutineScope does for you.
package workbench.coroutines.l03;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public class FailureSpreadsJava {
    static long t0;
    static void log(String msg) { System.out.printf("[%4d ms] %s%n", (System.nanoTime() - t0) / 1_000_000, msg); }

    public static void main(String[] args) throws InterruptedException {
        boolean cancelByHand = args.length > 0 && args[0].equals("cancel");
        t0 = System.nanoTime();
        try (ExecutorService children = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<?> ledger = children.submit(() -> {
                sleep(100);
                log("ledger: throwing IOException");
                throw new UncheckedIOException(new IOException("ledger unavailable"));
            });
            Future<?> risk = children.submit(() -> {
                try {
                    sleep(1_000);
                    log("risk: done");
                } finally {
                    log("risk: finally block runs");
                }
            });
            try {
                ledger.get();
            } catch (ExecutionException e) {
                log("caller caught: " + e.getCause().getCause().getMessage());
                if (cancelByHand) risk.cancel(true);   // interrupts the sibling
            }
        }   // close() waits for every task, including the sibling nobody cancelled
        log("executor closed");
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { throw new RuntimeException("interrupted", e); }
    }
}
