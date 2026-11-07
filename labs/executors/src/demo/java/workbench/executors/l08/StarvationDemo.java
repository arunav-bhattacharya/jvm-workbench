package workbench.executors.l08;

import java.util.List;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ForkJoinPool;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.IntStream;

/** Blocking BIN lookups in a parallel stream while a tiny task needs the common pool. Args: [blocking|managed|io]. */
public class StarvationDemo {
    static final long T0 = System.nanoTime();
    static final int PARALLELISM = ForkJoinPool.getCommonPoolParallelism();
    static final AtomicInteger STARTED = new AtomicInteger();
    static final CountDownLatch ALL_BUSY = new CountDownLatch(1);

    static void log(String msg) {
        System.out.printf("%5d ms  %s%n", (System.nanoTime() - T0) / 1_000_000, msg);
    }

    static void lookup() {
        if (STARTED.incrementAndGet() == PARALLELISM + 1) ALL_BUSY.countDown();   // the common pool and main are all busy
        sleep(300);                                              // a remote call
    }

    static void managedLookup() {
        try {
            // tells the pool this worker is about to block, so it can start a spare thread
            ForkJoinPool.managedBlock(new ForkJoinPool.ManagedBlocker() {
                boolean done;

                @Override
                public boolean block() {
                    lookup();
                    done = true;
                    return true;
                }

                @Override
                public boolean isReleasable() {
                    return done;
                }
            });
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    public static void main(String[] args) throws InterruptedException {
        String mode = args.length > 0 ? args[0] : "blocking";
        int lookups = (PARALLELISM + 1) * 4;                     // four rounds of work for the common pool and main
        log(mode + ": common pool parallelism " + PARALLELISM + ", " + lookups + " lookups of 300 ms");

        Thread fx = new Thread(() -> {
            try {
                ALL_BUSY.await();                                // start once the lookups are under way
            } catch (InterruptedException e) {
                return;
            }
            long t = System.nanoTime();
            String who = CompletableFuture.supplyAsync(() -> Thread.currentThread().getName()).join();   // a tiny task
            log("tiny task waited " + (System.nanoTime() - t) / 1_000_000 + " ms, then ran on " + who);
        });
        fx.start();

        if (mode.equals("io")) {
            try (ExecutorService io = Executors.newFixedThreadPool(lookups)) {
                List<CompletableFuture<Void>> calls = IntStream.range(0, lookups)
                        .mapToObj(i -> CompletableFuture.runAsync(StarvationDemo::lookup, io))
                        .toList();
                calls.forEach(CompletableFuture::join);
            }
        } else {
            boolean managed = mode.equals("managed");
            IntStream.range(0, lookups).parallel().forEach(i -> {
                if (managed) managedLookup();
                else lookup();
            });
        }
        log("all lookups done");
        fx.join();
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
