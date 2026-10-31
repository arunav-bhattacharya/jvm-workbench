package workbench.executors.l01;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;

/** shutdown, awaitTermination and shutdownNow on a pool of 2 threads with 6 queued 300 ms tasks. */
public class ShutdownDemo {
    static final long T0 = System.nanoTime();

    static void log(String msg) {
        System.out.printf("%5d ms  %s%n", (System.nanoTime() - T0) / 1_000_000, msg);
    }

    static Runnable settle(int id) {
        return () -> {
            try {
                Thread.sleep(300);                  // a 300 ms call to the ledger
                log("settled batch " + id);
            } catch (InterruptedException e) {
                log("batch " + id + " interrupted");
                Thread.currentThread().interrupt();
            }
        };
    }

    public static void main(String[] args) throws Exception {
        boolean now = args.length > 0 && args[0].equals("now");
        ExecutorService pool = Executors.newFixedThreadPool(2);
        for (int i = 1; i <= 6; i++) pool.execute(settle(i));

        if (now) {
            Thread.sleep(100);
            List<Runnable> neverStarted = pool.shutdownNow();
            log("shutdownNow returned " + neverStarted.size() + " tasks that never started");
        } else {
            pool.shutdown();
            log("shutdown returned. isShutdown=" + pool.isShutdown() + " isTerminated=" + pool.isTerminated());
        }

        try {
            pool.execute(settle(7));
        } catch (RejectedExecutionException e) {
            log("batch 7 rejected: the pool is shut down");
        }

        boolean done = pool.awaitTermination(5, TimeUnit.SECONDS);
        log("awaitTermination returned " + done + ". isTerminated=" + pool.isTerminated());
    }
}
