package workbench.executors.l06;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** Which thread runs the next stage? It depends on timing, and on the Async suffix. */
public class WhichThreadDemo {
    static String me() {
        return Thread.currentThread().getName();
    }

    public static void main(String[] args) {
        try (ExecutorService io = Executors.newFixedThreadPool(1, Thread.ofPlatform().name("io-", 1).factory());
             ExecutorService cpu = Executors.newFixedThreadPool(1, Thread.ofPlatform().name("cpu-", 1).factory())) {

            CompletableFuture<String> done = CompletableFuture.completedFuture("x");
            System.out.println("1. thenApply on a finished future:    " + done.thenApply(x -> me()).join());

            CompletableFuture<String> slow = CompletableFuture.supplyAsync(() -> { sleep(200); return "x"; }, io);
            CompletableFuture<String> attached = slow.thenApply(x -> me());       // attached while slow still runs
            System.out.println("2. thenApply attached while running:  " + attached.join());

            System.out.println("3. thenApplyAsync(fn):                " + slow.thenApplyAsync(x -> me()).join());
            System.out.println("4. thenApplyAsync(fn, cpu):           " + slow.thenApplyAsync(x -> me(), cpu).join());
        }
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
