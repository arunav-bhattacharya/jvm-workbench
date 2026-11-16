package workbench.executors.l07;

import java.math.BigDecimal;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

/** A 600 ms call to a slow supplier with orTimeout(200 ms). Pass "cancel" to try cancel(true) at 200 ms instead. */
public class KeepsRunningDemo {
    static final long T0 = System.nanoTime();

    static void log(String msg) {
        System.out.printf("%4d ms  %-38s %s%n", (System.nanoTime() - T0) / 1_000_000, Thread.currentThread().getName(), msg);
    }

    public static void main(String[] args) throws InterruptedException {
        boolean cancel = args.length > 0 && args[0].equals("cancel");
        try (ExecutorService io = Executors.newFixedThreadPool(1, Thread.ofPlatform().name("io-", 1).factory())) {
            CompletableFuture<BigDecimal> quote = CompletableFuture.supplyAsync(() -> {
                log("asking the slow supplier for a price");
                try {
                    Thread.sleep(600);
                } catch (InterruptedException e) {
                    log("interrupted: the call stops here");
                    throw new IllegalStateException(e);
                }
                log("the supplier answered, but nobody is listening");
                return new BigDecimal("19.80");
            }, io);

            if (cancel) {
                Thread.sleep(200);
                log("cancel(true) returned " + quote.cancel(true));
            } else {
                quote.orTimeout(200, TimeUnit.MILLISECONDS);
            }
            quote.handle((v, ex) -> {
                log("the future completed with " + (ex == null ? v : ex.getClass().getSimpleName()));
                return null;
            }).join();
        }   // close() waits for the supplier call, which is still running
        log("pool closed");
    }
}
