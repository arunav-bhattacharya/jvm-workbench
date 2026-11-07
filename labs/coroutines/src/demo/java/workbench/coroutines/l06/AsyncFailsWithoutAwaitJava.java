// Java equivalent of AsyncFailsWithoutAwait.kt: a failed CompletableFuture tells nobody.
// The failure sits in the future until someone joins it, and the sibling task runs on.
package workbench.coroutines.l06;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AsyncFailsWithoutAwaitJava {
    static final long T0 = System.nanoTime();
    static void log(String msg) { System.out.printf("%5d ms  %s%n", (System.nanoTime() - T0) / 1_000_000, msg); }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }

    public static void main(String[] args) {
        try (ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor()) {
            CompletableFuture<Void> risk = CompletableFuture.runAsync(() -> {
                sleep(100);
                throw new UncheckedIOException(new IOException("risk service down"));   // nobody joins this yet
            }, pool);
            CompletableFuture.runAsync(() -> {
                try { sleep(1_000); log("ledger: done"); } finally { log("ledger: finally"); }
            }, pool);
            sleep(500);
            log("body: still running at 500 ms, about to join risk");
            try {
                risk.join();
            } catch (CompletionException e) {
                log("caller caught: " + e.getCause().getCause().getMessage());
            }
        }   // close() waits for the ledger task, which nobody cancelled
        log("pool closed");
    }
}
