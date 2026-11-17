// Java equivalent of NotAMutex.kt: a single-thread executor runs one task at a time, but an
// async step (a CompletableFuture chain) lets the next helper start before the first one has
// written. A ReentrantLock held across the whole read-look-up-write keeps them apart, and unlike
// Kotlin's Mutex it IS reentrant.
package workbench.coroutines.l10;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.ReentrantLock;
import java.util.stream.IntStream;

public class NotAMutexJava {
    public static void main(String[] args) throws Exception {
        ExecutorService oneThread = Executors.newSingleThreadExecutor();
        System.out.println("single-thread executor:");
        List<CompletableFuture<Void>> helpers = IntStream.range(0, 3).mapToObj(i ->
            CompletableFuture.runAsync(() -> System.out.println("  helper " + i + ": read the list"), oneThread)
                // the recipe-app lookup is async: the thread is free while it waits
                .thenCompose(v -> CompletableFuture.runAsync(() -> { }, CompletableFuture.delayedExecutor(20, TimeUnit.MILLISECONDS)))
                .thenRunAsync(() -> System.out.println("  helper " + i + ": write the list"), oneThread)
        ).toList();
        CompletableFuture.allOf(helpers.toArray(CompletableFuture[]::new)).join();
        oneThread.shutdown();

        System.out.println("ReentrantLock around the whole addition:");
        ReentrantLock lock = new ReentrantLock();
        try (ExecutorService pool = Executors.newFixedThreadPool(3)) {
            for (int i = 0; i < 3; i++) {
                int n = i;
                pool.submit(() -> {
                    lock.lock();
                    try {
                        System.out.println("  helper " + n + ": read the list");
                        Thread.sleep(20); // a blocking lookup, inside the lock
                        System.out.println("  helper " + n + ": write the list");
                    } catch (InterruptedException e) {
                        Thread.currentThread().interrupt();
                    } finally {
                        lock.unlock();
                    }
                });
            }
        }

        System.out.println("ReentrantLock is reentrant:");
        lock.lock();
        try {
            lock.lock(); // the same thread takes it again
            try { System.out.println("  nested lock -> inner (hold count " + lock.getHoldCount() + ")"); }
            finally { lock.unlock(); }
        } finally {
            lock.unlock();
        }
    }
}
