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
            CompletableFuture<Void> audit = new CompletableFuture<>();
            loop.execute(() -> {                       // like launch: queued behind the running task
                System.out.println("C: audit starts");
                loop.schedule(() -> { System.out.println("F: audit written"); audit.complete(null); }, 100, TimeUnit.MILLISECONDS);
            });
            CompletableFuture<Long> price = new CompletableFuture<>();
            loop.execute(() -> {                       // like async
                System.out.println("D: price lookup starts");
                loop.schedule(() -> price.complete(1_084_512L), 50, TimeUnit.MILLISECONDS);
            });
            System.out.println("B: tasks queued, audit.isDone=" + audit.isDone());
            price.thenAccept(p -> System.out.println("E: price is " + p))   // like await, written as a callback
                 .thenCompose(x -> audit)                                   // like join
                 .thenRun(() -> {
                     System.out.println("G: audit.isDone=" + audit.isDone());
                     loop.shutdown();
                 });
        });
        loop.awaitTermination(5, TimeUnit.SECONDS);
    }
}
