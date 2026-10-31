package workbench.executors.l04;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

/** get(200 ms) on a call that takes 600 ms. Pass "cancel" to cancel(true) after the timeout. */
public class TimeoutDemo {
    static final long T0 = System.nanoTime();

    static void log(String msg) {
        System.out.printf("%4d ms  %-12s %s%n", (System.nanoTime() - T0) / 1_000_000, Thread.currentThread().getName(), msg);
    }

    public static void main(String[] args) throws Exception {
        boolean cancel = args.length > 0 && args[0].equals("cancel");
        try (ExecutorService pool = Executors.newFixedThreadPool(1)) {
            Future<String> auth = pool.submit(() -> {
                log("calling the issuer");
                try {
                    Thread.sleep(600);                    // the issuer is slow today
                } catch (InterruptedException e) {
                    log("interrupted: giving up on the issuer");
                    throw e;
                }
                log("issuer answered: APPROVED (and the charge went through)");
                return "APPROVED";
            });
            try {
                log("result: " + auth.get(200, TimeUnit.MILLISECONDS));
            } catch (TimeoutException e) {
                log("get timed out after 200 ms");
                if (cancel) log("cancel(true) returned " + auth.cancel(true));
            }
        }   // close() waits for the task, which is still running unless we cancelled it
        log("pool closed");
    }
}
