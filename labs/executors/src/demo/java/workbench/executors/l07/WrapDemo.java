package workbench.executors.l07;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** Which exception does each handler see? Predict every line before you run it. */
public class WrapDemo {
    static String describe(Throwable ex) {
        String name = ex.getClass().getSimpleName();
        return ex.getCause() == null ? name : name + " <- " + ex.getCause().getClass().getSimpleName();
    }

    static void show(String label, CompletableFuture<?> f) {
        String seen = f.handle((v, ex) -> describe(ex)).join();
        System.out.printf("%-42s %s%n", label, seen);
    }

    public static void main(String[] args) {
        IllegalStateException down = new IllegalStateException("502");
        try (ExecutorService io = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("io-", 1).factory())) {
            CompletableFuture<String> supplied = CompletableFuture.supplyAsync(() -> { throw down; }, io);
            CompletableFuture<String> completed = new CompletableFuture<>();
            completed.completeExceptionally(down);
            CompletableFuture<String> timedOut = CompletableFuture.supplyAsync(() -> sleepThen(1000, "late"), io)
                    .orTimeout(100, TimeUnit.MILLISECONDS);

            show("1. handle() on the supplyAsync future", supplied);
            show("2. handle() on completeExceptionally", completed);
            show("3. handle() one stage later", completed.thenApply(String::trim));
            show("4. handle() after orTimeout", timedOut);
            try {
                supplied.get();
            } catch (ExecutionException | InterruptedException e) {
                System.out.printf("%-42s %s%n", "5. get() throws", describe(e));
            }
            try {
                supplied.join();
            } catch (CompletionException e) {
                System.out.printf("%-42s %s%n", "6. join() throws", describe(e));
            }
        }
    }

    static String sleepThen(long ms, String value) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return value;
    }
}
