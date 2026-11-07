// Java equivalent of TimeoutsAndBlocking.kt: a timeout on a CompletableFuture gives the caller
// an answer on time, but nothing stops the blocking task. Future.cancel(true) interrupts it.
package workbench.coroutines.l05;

import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionException;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.TimeoutException;

public class TimeoutsAndBlockingJava {
    static long t0;

    static String callIssuer() {
        try {
            Thread.sleep(1_500); // the issuer takes 1.5 s
            System.out.printf("    (the issuer call itself finished at %d ms)%n", ms());
            return "approved";
        } catch (InterruptedException e) {
            System.out.printf("    (the issuer call was interrupted at %d ms)%n", ms());
            return "interrupted";
        }
    }

    static long ms() { return (System.nanoTime() - t0) / 1_000_000; }

    public static void main(String[] args) throws Exception {
        try (ExecutorService io = Executors.newCachedThreadPool()) {
            // 1. orTimeout: the caller gets a TimeoutException on time, the task runs on
            t0 = System.nanoTime();
            try {
                CompletableFuture.supplyAsync(TimeoutsAndBlockingJava::callIssuer, io).orTimeout(300, TimeUnit.MILLISECONDS).join();
            } catch (CompletionException e) {
                System.out.printf("orTimeout(300 ms)               caller got %s after %d ms%n", e.getCause().getClass().getSimpleName(), ms());
            }
            Thread.sleep(1_400); // wait, to see the abandoned task finish anyway

            // 2. Future.get with a timeout, then cancel(true): the blocked thread is interrupted
            t0 = System.nanoTime();
            Future<String> f = io.submit(TimeoutsAndBlockingJava::callIssuer);
            try {
                f.get(300, TimeUnit.MILLISECONDS);
            } catch (TimeoutException e) {
                f.cancel(true);
                System.out.printf("get(300 ms) + cancel(true)      caller gave up after %d ms%n", ms());
            }
            Thread.sleep(100);
        }
    }
}
