package workbench.concurrency.l09;

import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.function.Consumer;

/** 8 threads count 800,000 payments over 1,000 merchants, three ways. Only one way is right. */
public class MapShootout {
    static void run(String label, Map<String, Integer> counts, Consumer<String> countOne) throws InterruptedException {
        CountDownLatch go = new CountDownLatch(1);
        Thread[] ts = new Thread[8];
        String[] error = new String[1];
        for (int i = 0; i < ts.length; i++) {
            ts[i] = new Thread(() -> {
                try {
                    go.await();
                    for (int n = 0; n < 100_000; n++) countOne.accept("m-" + (n % 1_000));
                } catch (Throwable e) {
                    error[0] = e.getClass().getSimpleName();
                }
            });
            ts[i].setDaemon(true);                       // a corrupted HashMap can even loop forever
            ts[i].start();
        }
        go.countDown();
        for (Thread t : ts) t.join(5_000);
        long total = 0;
        try {
            for (int v : counts.values()) total += v;
        } catch (Throwable e) {
            error[0] = e.getClass().getSimpleName();
        }
        System.out.printf("%-32s total %,9d of 800,000   keys %,5d of 1,000%s%n", label, total, counts.size(),
                error[0] == null ? "" : "   threw " + error[0]);
    }

    public static void main(String[] args) throws InterruptedException {
        Map<String, Integer> plain = new HashMap<>();
        run("HashMap.merge", plain, k -> plain.merge(k, 1, Integer::sum));

        Map<String, Integer> chm1 = new ConcurrentHashMap<>();
        run("ConcurrentHashMap get then put", chm1, k -> chm1.put(k, chm1.getOrDefault(k, 0) + 1));

        Map<String, Integer> chm2 = new ConcurrentHashMap<>();
        run("ConcurrentHashMap.merge", chm2, k -> chm2.merge(k, 1, Integer::sum));
    }
}
