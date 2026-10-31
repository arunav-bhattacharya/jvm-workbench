package workbench.executors.l05;

import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.ScheduledFuture;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicInteger;

/** A health check every 100 ms that throws on its third run. Pass "safe" to catch inside the task. */
public class SilentDeathDemo {
    public static void main(String[] args) throws Exception {
        boolean safe = args.length > 0 && args[0].equals("safe");
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        AtomicInteger runs = new AtomicInteger();
        Runnable check = () -> {
            int n = runs.incrementAndGet();
            System.out.println("health check " + n);
            if (n == 3) throw new IllegalStateException("ledger ping timed out");
        };
        Runnable task = !safe ? check : () -> {
            try {
                check.run();
            } catch (RuntimeException e) {
                System.out.println("  caught and logged: " + e.getMessage());
            }
        };
        ScheduledFuture<?> f = scheduler.scheduleAtFixedRate(task, 0, 100, TimeUnit.MILLISECONDS);

        Thread.sleep(1_000);                              // ten periods
        System.out.println("after 1 s: runs=" + runs.get() + " isDone=" + f.isDone());
        if (f.isDone()) {
            try {
                f.get();
            } catch (ExecutionException e) {
                System.out.println("get() threw ExecutionException, cause: " + e.getCause());
            }
        }
        scheduler.shutdownNow();
    }
}
