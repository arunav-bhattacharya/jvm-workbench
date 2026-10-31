// Java equivalent of BlockingOnDefault.kt: blocking calls on the common pool (sized for CPU work)
// versus on a separate pool for blocking work. Pass "io" to use the separate pool.
package workbench.coroutines.l04;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ForkJoinPool;

public class BlockingOnDefaultJava {
    public static void main(String[] args) throws Exception {
        boolean onIo = args.length > 0 && args[0].equals("io");
        int cores = Runtime.getRuntime().availableProcessors();
        ExecutorService io = Executors.newFixedThreadPool(64);
        // a pool sized like the common pool, so the demo behaves the same on every machine
        ForkJoinPool cpu = new ForkJoinPool(Math.max(2, cores));
        var blockingPool = onIo ? io : cpu;
        long t0 = System.nanoTime();
        List<CompletableFuture<Void>> calls = new ArrayList<>();
        for (int i = 0; i < 32; i++) {
            calls.add(CompletableFuture.runAsync(() -> sleep(200), blockingPool)); // JDBC-style blocking calls
        }
        Thread.sleep(20);
        long asked = System.nanoTime();
        long started = CompletableFuture.supplyAsync(System::nanoTime, cpu).join(); // tiny CPU task on the CPU pool
        CompletableFuture.allOf(calls.toArray(CompletableFuture[]::new)).join();
        System.out.printf("32 blocking calls on %s (%d cores): %d ms%n", onIo ? "a 64-thread pool" : "the CPU pool", cores,
            (System.nanoTime() - t0) / 1_000_000);
        System.out.printf("a tiny CPU task on the CPU pool waited %d ms to start%n", (started - asked) / 1_000_000);
        io.shutdown();
        cpu.shutdown();
    }

    static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
