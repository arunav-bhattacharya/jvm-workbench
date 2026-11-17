// Java equivalent of AsyncFailsWithoutAwait.kt: a failed CompletableFuture tells nobody.
// The failure sits in the future until someone joins it, and the sibling task runs on.
package workbench.coroutines.l06;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class AsyncFailsWithoutAwaitJava {
    static class BurnedException extends RuntimeException {
        BurnedException(String message) { super(message); }
    }

    static long T0;
    static void log(String msg) { System.out.printf("%5d ms  %s%n", (System.nanoTime() - T0) / 1_000_000, msg); }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }

    public static void main(String[] args) {
        T0 = System.nanoTime();
        try (ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor()) {
            CompletableFuture<Void> gravy = CompletableFuture.runAsync(() -> {
                sleep(100);
                throw new BurnedException("the gravy burned");   // nobody joins this yet
            }, pool);
            CompletableFuture.runAsync(() -> {
                try { sleep(1_000); log("potatoes: done"); } finally { log("potatoes: finally"); }
            }, pool);
            sleep(500);
            log("body: still running at 500 ms, about to join the gravy");
            try {
                gravy.join();
            } catch (CompletionException e) {
                log("caller caught: " + e.getCause().getMessage());
            }
        }   // close() waits for the potatoes, which nobody cancelled
        log("pool closed");
    }
}
