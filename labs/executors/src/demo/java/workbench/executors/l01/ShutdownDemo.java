package workbench.executors.l01;

import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.TimeUnit;

/** shutdown, awaitTermination and shutdownNow on a kitchen of 2 cooks (threads) with 6 orders of 300 ms each. */
public class ShutdownDemo {
    static final long T0 = System.nanoTime();

    static void log(String msg) {
        System.out.printf("%5d ms  %s%n", (System.nanoTime() - T0) / 1_000_000, msg);
    }

    static Runnable cook(int id) {
        return () -> {
            try {
                Thread.sleep(300);                  // 300 ms to cook one order
                log("cooked order " + id);
            } catch (InterruptedException e) {
                log("order " + id + " interrupted");
                Thread.currentThread().interrupt();
            }
        };
    }

    public static void main(String[] args) throws Exception {
        boolean now = args.length > 0 && args[0].equals("now");
        ExecutorService pool = Executors.newFixedThreadPool(2);
        for (int i = 1; i <= 6; i++) pool.execute(cook(i));

        if (now) {
            Thread.sleep(100);
            List<Runnable> neverStarted = pool.shutdownNow();
            log("shutdownNow returned " + neverStarted.size() + " tasks that never started");
        } else {
            pool.shutdown();
            log("shutdown returned. isShutdown=" + pool.isShutdown() + " isTerminated=" + pool.isTerminated());
        }

        try {
            pool.execute(cook(7));
        } catch (RejectedExecutionException e) {
            log("order 7 rejected: the kitchen is closed");
        }

        boolean done = pool.awaitTermination(5, TimeUnit.SECONDS);
        log("awaitTermination returned " + done + ". isTerminated=" + pool.isTerminated());
    }
}
