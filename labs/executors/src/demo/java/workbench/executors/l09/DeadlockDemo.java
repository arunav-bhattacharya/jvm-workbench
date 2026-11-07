package workbench.executors.l09;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** Two statement tasks on a 2-thread pool, each waiting for a fetch on the same pool. Pass "fixed" to compose instead. */
public class DeadlockDemo {
    static List<String> fetchLines(String merchant) {
        return List.of(merchant + "-1", merchant + "-2");               // fast: the problem isn't speed
    }

    public static void main(String[] args) throws Exception {
        boolean fixed = args.length > 0 && args[0].equals("fixed");
        ExecutorService pool = Executors.newFixedThreadPool(2, Thread.ofPlatform().name("stmt-", 0).factory());
        try {
            if (fixed) {
                List<CompletableFuture<String>> statements = List.of("m1", "m2").stream()
                        .map(m -> CompletableFuture.supplyAsync(() -> fetchLines(m), pool)
                                .thenApply(lines -> m + ": " + lines.size() + " lines"))   // nobody waits inside the pool
                        .toList();
                statements.forEach(s -> System.out.println(s.join()));
                return;
            }
            List<Future<String>> statements = List.of("m1", "m2").stream()
                    .map(m -> pool.submit(() -> {
                        Future<List<String>> lines = pool.submit(() -> fetchLines(m));   // queued behind us
                        return m + ": " + lines.get().size() + " lines";             // waits for it
                    }))
                    .toList();
            Thread.sleep(300);
            ThreadPoolExecutor tpe = (ThreadPoolExecutor) pool;
            System.out.printf("after 300 ms: active=%d, queued=%d, completed=%d%n",
                    tpe.getActiveCount(), tpe.getQueue().size(), tpe.getCompletedTaskCount());
            try {
                System.out.println(statements.get(0).get(2, TimeUnit.SECONDS));
            } catch (TimeoutException e) {
                System.out.println("no statement after 2 s: both threads wait for fetches that can never start");
            }
        } finally {
            pool.shutdownNow();                                           // interrupts the stuck get() calls
        }
    }
}
