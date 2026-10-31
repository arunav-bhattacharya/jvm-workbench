// Java equivalent of WhereDoesItRun.kt: in Java you pick an executor for each step yourself.
package workbench.coroutines.l04;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.TimeUnit;

public class WhereDoesItRunJava {
    static String here() { return Thread.currentThread().toString(); }

    public static void main(String[] args) {
        System.out.println("main                  " + here());
        // the common pool: one thread per core, the closest match for Dispatchers.Default
        CompletableFuture.runAsync(() -> System.out.println("commonPool            " + here()), ForkJoinPool.commonPool()).join();
        // a cached pool grows for blocking work, roughly what Dispatchers.IO does (without the cap)
        ExecutorService cached = Executors.newCachedThreadPool();
        CompletableFuture.runAsync(() -> System.out.println("cached pool           " + here()), cached).join();
        cached.shutdown();
        // a non-async stage runs on whichever thread completes the previous stage, like Unconfined
        CompletableFuture.supplyAsync(() -> 1, CompletableFuture.delayedExecutor(10, TimeUnit.MILLISECONDS))
            .thenAccept(x -> System.out.println("thenAccept after timer " + here()))
            .join();
        try (ExecutorService single = Executors.newSingleThreadExecutor(r -> new Thread(r, "ledger-writer"))) {
            CompletableFuture.runAsync(() -> System.out.println("single-thread exec    " + here()), single).join();
        }
        try (ExecutorService vt = Executors.newVirtualThreadPerTaskExecutor()) {
            CompletableFuture.runAsync(() -> System.out.println("virtual-thread exec   " + here()), vt).join();
        }
    }
}
