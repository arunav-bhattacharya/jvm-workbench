// Java equivalent of SupervisorDemo.kt: CompletableFutures are independent by default, like
// children of a supervisor. Nothing cancels the siblings, so each future handles its own failure.
package workbench.coroutines.l06;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class SupervisorDemoJava {
    static long started;
    static void log(String msg) { System.out.printf("%5d ms  %s%n", (System.nanoTime() - started) / 1_000_000, msg); }
    static void sleep(long ms) { try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); } }

    public static void main(String[] args) {
        started = System.nanoTime();
        try (ExecutorService pool = Executors.newVirtualThreadPerTaskExecutor()) {
            CompletableFuture<Void> email = CompletableFuture.runAsync(() -> { sleep(300); log("email sent"); }, pool);
            CompletableFuture<Void> sms = CompletableFuture.runAsync(() -> {
                sleep(50);
                throw new UncheckedIOException(new IOException("sms gateway down"));
            }, pool);
            CompletableFuture<Void> push = CompletableFuture.runAsync(() -> { sleep(100); log("push sent"); }, pool);
            // each failure is handled where it happens; the siblings never hear about it
            CompletableFuture<Void> smsHandled = sms.exceptionally(e -> { log("handled: " + e.getCause().getCause().getMessage()); return null; });
            CompletableFuture.allOf(email, smsHandled, push).join();
            log("all three settled");
        }
    }
}
