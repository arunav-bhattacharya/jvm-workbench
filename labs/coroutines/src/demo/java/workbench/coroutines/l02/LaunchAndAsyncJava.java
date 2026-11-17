// Java equivalent of LaunchAndAsync.kt: one event-loop thread, tasks queue behind the running one.
// Java has no suspension, so "await" becomes a callback (thenAccept) instead of a pause.
package workbench.coroutines.l02;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

public class LaunchAndAsyncJava {
    public static void main(String[] args) throws InterruptedException {
        ScheduledExecutorService loop = Executors.newSingleThreadScheduledExecutor(r -> new Thread(r, "loop"));
        loop.execute(() -> {
            System.out.println("A: before the tasks");
            CompletableFuture<Void> table = new CompletableFuture<>();
            loop.execute(() -> {                       // like launch: queued behind the running task
                System.out.println("C: table: start setting it");
                loop.schedule(() -> { System.out.println("F: table: set"); table.complete(null); }, 100, TimeUnit.MILLISECONDS);
            });
            CompletableFuture<Integer> oven = new CompletableFuture<>();
            loop.execute(() -> {                       // like async
                System.out.println("D: oven: checking the temperature");
                loop.schedule(() -> oven.complete(180), 50, TimeUnit.MILLISECONDS);
            });
            System.out.println("B: tasks queued, table.isDone=" + table.isDone());
            oven.thenAccept(t -> System.out.println("E: oven is at " + t + " degrees"))   // like await, written as a callback
                .thenCompose(x -> table)                                               // like join
                .thenRun(() -> {
                    System.out.println("G: table.isDone=" + table.isDone());
                    loop.shutdown();
                });
        });
        loop.awaitTermination(5, TimeUnit.SECONDS);
    }
}
