// Java equivalent of CallbackBridge.kt: wrap the callback SDK in a CompletableFuture.
// The SDK answers after 1 second; the caller allows 100 ms.
package workbench.coroutines.l01;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;
import java.util.function.IntConsumer;

public class CallbackBridgeJava {
    /** A fraud-scoring SDK with a callback API. It answers after 1 second on its own thread. */
    static final class Sdk {
        private final ScheduledExecutorService pool = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "fraud-sdk");
            t.setDaemon(true);
            return t;
        });

        Runnable score(String paymentId, IntConsumer onScore) {
            ScheduledFuture<?> task = pool.schedule(() -> onScore.accept(17), 1, TimeUnit.SECONDS);
            return () -> {
                System.out.println("  sdk: request for " + paymentId + " cancelled");
                task.cancel(false);
            };
        }
    }

    // Wrapped as a future: the caller can time out, but nothing tells the SDK yet.
    static CompletableFuture<Integer> scoreAsync(Sdk sdk, String paymentId) {
        CompletableFuture<Integer> result = new CompletableFuture<>();
        Runnable cancel = sdk.score(paymentId, result::complete);
        return result;
    }

    public static void main(String[] args) {
        Sdk sdk = new Sdk();
        long t0 = System.nanoTime();
        try {
            scoreAsync(sdk, "pay_981").orTimeout(100, TimeUnit.MILLISECONDS).join();
        } catch (CompletionException e) {
            if (e.getCause() instanceof TimeoutException) System.out.println("  timed out");
        }
        System.out.printf("orTimeout(100) returned after %d ms%n", (System.nanoTime() - t0) / 1_000_000);
        try { Thread.sleep(1_100); } catch (InterruptedException ignored) { }   // was the SDK told?
    }
}
