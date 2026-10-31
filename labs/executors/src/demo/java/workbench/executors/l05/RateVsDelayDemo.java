package workbench.executors.l05;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** A 100 ms schedule whose second run takes 250 ms. Default: fixed rate. Pass "delay" for fixed delay. */
public class RateVsDelayDemo {
    public static void main(String[] args) throws Exception {
        boolean delay = args.length > 0 && args[0].equals("delay");
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        AtomicInteger runs = new AtomicInteger();
        CountDownLatch sevenRuns = new CountDownLatch(7);
        long t0 = System.nanoTime();
        Runnable sync = () -> {
            int n = runs.incrementAndGet();
            long start = (System.nanoTime() - t0) / 1_000_000;
            long work = n == 2 ? 250 : 10;                // run 2 hits a slow ledger
            try { Thread.sleep(work); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            System.out.printf("run %d started at %4d ms, took %3d ms%n", n, start, work);
            sevenRuns.countDown();
        };
        ScheduledFuture<?> f = delay
                ? scheduler.scheduleWithFixedDelay(sync, 0, 100, TimeUnit.MILLISECONDS)
                : scheduler.scheduleAtFixedRate(sync, 0, 100, TimeUnit.MILLISECONDS);
        System.out.println(delay ? "scheduleWithFixedDelay, 100 ms" : "scheduleAtFixedRate, 100 ms");
        sevenRuns.await();
        f.cancel(false);
        scheduler.shutdown();
    }
}
