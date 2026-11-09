package workbench.functional.l02.demo;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;

/**
 * Java twin of CapturedRace.kt. Java refuses to capture a local that changes:
 *   long total = 0; ... () -> total += 1
 *   error: local variables referenced from a lambda expression must be final or effectively final
 * So Java programmers write the box by hand, a one-element array. That is what Kotlin's Ref.LongRef is.
 */
public class CapturedRaceJava {
    public static void main(String[] args) throws Exception {
        ExecutorService pool = Executors.newFixedThreadPool(4);
        for (int run = 1; run <= 10; run++) {
            long[] total = {0};                              // the hand-made box: a plain array slot
            CountDownLatch go = new CountDownLatch(1);       // start all four tasks at the same moment
            List<Future<?>> tasks = new ArrayList<>();
            for (int t = 0; t < 4; t++) {
                tasks.add(pool.submit(() -> {
                    go.await();
                    for (int i = 0; i < 250_000; i++) total[0] += 1;   // read, add 1, write
                    return null;
                }));
            }
            go.countDown();
            for (Future<?> f : tasks) f.get();
            System.out.printf("run %2d: expected 1,000,000, got %,9d (lost %,d)%n", run, total[0], 1_000_000 - total[0]);
        }
        pool.shutdown();
    }
}
