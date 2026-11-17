// Java equivalent of FanOutFanIn.kt: a fixed pool takes tasks from its queue (fan-out), and an
// ExecutorCompletionService hands back results in the order they finish (fan-in).
package workbench.coroutines.l09;

import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ExecutorCompletionService;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ThreadLocalRandom;

public class FanOutFanInJava {
    public static void main(String[] args) throws Exception {
        int helpers = args.length > 0 ? Integer.parseInt(args[0]) : 4;
        long t0 = System.nanoTime();
        try (ExecutorService pool = Executors.newFixedThreadPool(helpers)) {
            ExecutorCompletionService<String> table = new ExecutorCompletionService<>(pool);
            for (int i = 1; i <= 20; i++) {
                String dish = "dish-" + i;
                table.submit(() -> {
                    Thread.sleep(ThreadLocalRandom.current().nextLong(50, 150)); // carrying it, serving it
                    return dish + " by " + Thread.currentThread().getName();
                });
            }
            Map<String, Integer> perHelper = new TreeMap<>();
            for (int i = 0; i < 20; i++) perHelper.merge(table.take().get().split(" by ")[1], 1, Integer::sum);
            System.out.println(helpers + " helpers: " + perHelper);
        }
        System.out.println("20 dishes took " + (System.nanoTime() - t0) / 1_000_000 + " ms");
    }
}
