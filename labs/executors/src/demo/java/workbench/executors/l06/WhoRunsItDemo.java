package workbench.executors.l06;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ForkJoinPool;

/** Which thread runs supplyAsync? Pass "1cpu" to size the common pool the way a 2-CPU container does. */
public class WhoRunsItDemo {
    public static void main(String[] args) {
        if (args.length > 0 && args[0].equals("1cpu")) {
            // must run before anything touches ForkJoinPool: a 2-CPU container gets parallelism 1
            System.setProperty("java.util.concurrent.ForkJoinPool.common.parallelism", "1");
        }
        System.out.println("JDK " + Runtime.version().feature()
                + ", common pool parallelism " + ForkJoinPool.getCommonPoolParallelism());

        for (int i = 0; i < 3; i++) {
            String who = CompletableFuture.supplyAsync(() -> Thread.currentThread().getName()).join();
            System.out.println("supplyAsync(task)      ran on " + who);
        }
        try (ExecutorService io = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("io-", 1).factory())) {
            for (int i = 0; i < 3; i++) {
                String who = CompletableFuture.supplyAsync(() -> Thread.currentThread().getName(), io).join();
                System.out.println("supplyAsync(task, io)  ran on " + who);
            }
        }
    }
}
