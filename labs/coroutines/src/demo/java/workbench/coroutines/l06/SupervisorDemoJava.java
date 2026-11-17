// Java equivalent of SupervisorDemo.kt: CompletableFutures are independent by default, like
// children of a supervisor. Nothing cancels the siblings, so each future handles its own failure.
package workbench.coroutines.l06;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SupervisorDemoJava {
    static class BurnedException extends RuntimeException {
        BurnedException(String message) { super(message); }
    }

    static long started;
    static void log(String msg) { System.out.printf("%5d ms  %s%n", (System.nanoTime() - started) / 1_000_000, msg); }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }

    public static void main(String[] args) {
        started = System.nanoTime();
        try (ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor()) {
            // three trays for the bake sale, all in the oven at once
            CompletableFuture<Void> cookies = CompletableFuture.runAsync(() -> { sleep(300); log("cookies baked"); }, pool);
            CompletableFuture<Void> scones = CompletableFuture.runAsync(() -> {
                sleep(50);
                throw new BurnedException("the scones burned");
            }, pool);
            CompletableFuture<Void> muffins = CompletableFuture.runAsync(() -> { sleep(100); log("muffins baked"); }, pool);
            // each failure is handled where it happens; the siblings never hear about it
            CompletableFuture<Void> sconesHandled = scones.exceptionally(e -> { log("handled: " + e.getCause().getMessage()); return null; });
            CompletableFuture.allOf(cookies, sconesHandled, muffins).join();
            log("all three trays are out");
        }
    }
}
