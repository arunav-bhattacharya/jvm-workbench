// Java equivalent of FailureSpreads.kt with a virtual-thread executor (JDK 21+, no preview APIs).
// An executor has no parent-child tree: a failed task does not cancel its sibling unless you do it.
// Pass "cancel" to cancel the sibling by hand, which is what coroutineScope does for you.
package workbench.coroutines.l03;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

public class FailureSpreadsJava {
    /** A dish that went wrong. */
    static final class BurnedException extends RuntimeException {
        BurnedException(String message) { super(message); }
    }

    static long t0;
    static void log(String msg) { System.out.printf("[%4d ms] %s%n", (System.nanoTime() - t0) / 1_000_000, msg); }

    public static void main(String[] args) throws InterruptedException {
        boolean cancelByHand = args.length > 0 && args[0].equals("cancel");
        t0 = System.nanoTime();
        try (ExecutorService children = Executors.newVirtualThreadPerTaskExecutor()) {
            Future<?> roast = children.submit(() -> {
                sleep(100);
                log("roast: burned, throwing BurnedException");
                throw new BurnedException("the roast burned");
            });
            Future<?> potatoes = children.submit(() -> {
                try {
                    sleep(1_000);
                    log("potatoes: done");
                } finally {
                    log("potatoes: finally block runs");
                }
            });
            try {
                roast.get();
            } catch (ExecutionException e) {
                log("caller caught: " + e.getCause().getMessage());
                if (cancelByHand) potatoes.cancel(true);   // interrupts the sibling
            }
        }   // close() waits for every task, including the sibling nobody cancelled
        log("executor closed");
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { throw new RuntimeException("interrupted", e); }
    }
}
