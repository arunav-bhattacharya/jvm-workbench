// Java equivalent of SelectFirst.kt: CompletableFuture.anyOf completes with the first future to
// finish, and completeOnTimeout supplies a fallback. Cancelling the losers is up to you.
package workbench.coroutines.l09;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class SelectFirstJava {
    static String answer(String text, long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
        return text;
    }

    public static void main(String[] args) {
        long t0 = System.nanoTime();
        long budgetMs = args.length > 0 ? Long.parseLong(args[0]) : 500;
        try (ExecutorService phones = Executors.newVirtualThreadPerTaskExecutor()) {
            CompletableFuture<String> corner = CompletableFuture.supplyAsync(() -> answer("corner bakery: one rye loaf left", 300), phones);
            CompletableFuture<String> market = CompletableFuture.supplyAsync(() -> answer("market bakery: plenty of sourdough", 120), phones);
            Object answer = CompletableFuture.anyOf(corner, market)
                .completeOnTimeout("nobody answered within " + budgetMs + " ms: we bake our own bread", budgetMs, TimeUnit.MILLISECONDS)
                .join();
            corner.cancel(true); market.cancel(true); // only marks the futures; the calls may run on
            System.out.printf("after %d ms: %s%n", (System.nanoTime() - t0) / 1_000_000, answer);
            phones.shutdownNow();
        }
    }
}
