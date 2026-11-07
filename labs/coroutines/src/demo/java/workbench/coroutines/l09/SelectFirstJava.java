// Java equivalent of SelectFirst.kt: CompletableFuture.anyOf completes with the first future to
// finish, and completeOnTimeout supplies a fallback. Cancelling the losers is up to you.
package workbench.coroutines.l09;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class SelectFirstJava {
    static String quote(String text, long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return text;
    }

    public static void main(String[] args) {
        long t0 = System.nanoTime();
        long budgetMs = args.length > 0 ? Long.parseLong(args[0]) : 500;
        try (ExecutorService io = Executors.newVirtualThreadPerTaskExecutor()) {
            CompletableFuture<String> north = CompletableFuture.supplyAsync(() -> quote("north: 1.80%", 300), io);
            CompletableFuture<String> east = CompletableFuture.supplyAsync(() -> quote("east: 2.10%", 120), io);
            Object answer = CompletableFuture.anyOf(north, east)
                .completeOnTimeout("no quote within " + budgetMs + " ms: use the default acquirer", budgetMs, TimeUnit.MILLISECONDS)
                .join();
            north.cancel(true); east.cancel(true); // only marks the futures; the tasks may run on
            System.out.printf("after %d ms: %s%n", (System.nanoTime() - t0) / 1_000_000, answer);
            io.shutdownNow();
        }
    }
}
