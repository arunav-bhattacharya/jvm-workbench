// Java equivalent of RunBlockingTrap.kt: blocking on a future inside a task on a small pool.
// Pass "bad" to join inside the task, like calling runBlocking inside suspend code.
package workbench.coroutines.l02;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Executor;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class RunBlockingTrapJava {
    // a 200 ms lookup that completes from a timer: it holds no thread while it waits
    static CompletableFuture<Integer> lookup(int id, Executor pool) {
        Executor after200ms = CompletableFuture.delayedExecutor(200, TimeUnit.MILLISECONDS, pool);
        return CompletableFuture.supplyAsync(() -> id, after200ms);
    }

    public static void main(String[] args) {
        boolean bad = args.length > 0 && args[0].equals("bad");
        ExecutorService pool = Executors.newFixedThreadPool(2);   // a small request pool
        long t0 = System.nanoTime();
        List<CompletableFuture<Integer>> all = new ArrayList<>();
        for (int id = 0; id < 8; id++) {
            int i = id;
            all.add(bad
                ? CompletableFuture.supplyAsync(() -> lookup(i, pool).join(), pool)  // holds a pool thread for 200 ms
                : CompletableFuture.supplyAsync(() -> i, pool).thenCompose(x -> lookup(x, pool)));
        }
        CompletableFuture.allOf(all.toArray(CompletableFuture[]::new)).join();
        System.out.printf("8 lookups of 200 ms on 2 threads (%s): %d ms%n", bad ? "join inside the task" : "thenCompose",
            (System.nanoTime() - t0) / 1_000_000);
        pool.shutdown();
    }
}
