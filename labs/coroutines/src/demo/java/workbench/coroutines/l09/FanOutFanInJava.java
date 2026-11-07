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
        int workers = args.length > 0 ? Integer.parseInt(args[0]) : 4;
        long t0 = System.nanoTime();
        try (ExecutorService pool = Executors.newFixedThreadPool(workers)) {
            ExecutorCompletionService<String> results = new ExecutorCompletionService<>(pool);
            for (int i = 1; i <= 20; i++) {
                String id = "refund-" + i;
                results.submit(() -> {
                    Thread.sleep(ThreadLocalRandom.current().nextLong(50, 150)); // the issuer call
                    return id + " by " + Thread.currentThread().getName();
                });
            }
            Map<String, Integer> perWorker = new TreeMap<>();
            for (int i = 0; i < 20; i++) perWorker.merge(results.take().get().split(" by ")[1], 1, Integer::sum);
            System.out.println(workers + " workers: " + perWorker);
        }
        System.out.println("20 refunds took " + (System.nanoTime() - t0) / 1_000_000 + " ms");
    }
}
