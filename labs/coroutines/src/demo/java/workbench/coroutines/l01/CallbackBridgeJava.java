// Java equivalent of CallbackBridge.kt: wrap the bakery's callback library in a CompletableFuture.
// The bakery answers after 1 second; the caller allows 100 ms.
package workbench.coroutines.l01;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.Consumer;

public class CallbackBridgeJava {
    /** A bakery's ordering library with a callback API. It answers after 1 second, on its own thread. */
    static final class Sdk {
        private final ScheduledExecutorService pool = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "bakery-sdk");
            t.setDaemon(true);
            return t;
        });

        Runnable order(String bread, Consumer<String> onReady) {
            ScheduledFuture<?> task = pool.schedule(() -> onReady.accept("ticket 17: one " + bread), 1, TimeUnit.SECONDS);
            return () -> {
                System.out.println("  bakery: order for " + bread + " cancelled");
                task.cancel(false);
            };
        }
    }

    // Wrapped as a future: the caller can time out, but nothing tells the bakery yet.
    static CompletableFuture<String> orderAsync(Sdk bakery, String bread) {
        CompletableFuture<String> result = new CompletableFuture<>();
        Runnable cancel = bakery.order(bread, result::complete);
        return result;
    }

    public static void main(String[] args) {
        Sdk bakery = new Sdk();
        long t0 = System.nanoTime();
        try {
            orderAsync(bakery, "sourdough").orTimeout(100, TimeUnit.MILLISECONDS).join();
        } catch (CompletionException e) {
            if (e.getCause() instanceof TimeoutException) System.out.println("  timed out");
        }
        System.out.printf("orTimeout(100) returned after %d ms%n", (System.nanoTime() - t0) / 1_000_000);
        try { Thread.sleep(1_100); } catch (InterruptedException ignored) { }   // was the bakery told?
    }
}
