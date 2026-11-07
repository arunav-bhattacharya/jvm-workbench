package workbench.executors.l06;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** The price and the FX rate take 300 ms each. Pass "chain" to fetch them one after the other. */
public class CombineDemo {
    static final long T0 = System.nanoTime();

    static void log(String msg) {
        System.out.printf("%4d ms  %-6s %s%n", (System.nanoTime() - T0) / 1_000_000, Thread.currentThread().getName(), msg);
    }

    static BigDecimal priceEur() {
        sleep(300);                                        // the cart service
        log("price is 100.00 EUR");
        return new BigDecimal("100.00");
    }

    static BigDecimal eurToUsd() {
        sleep(300);                                        // the FX provider
        log("rate is 1.0842");
        return new BigDecimal("1.0842");
    }

    public static void main(String[] args) {
        boolean chain = args.length > 0 && args[0].equals("chain");
        try (ExecutorService io = Executors.newFixedThreadPool(4, Thread.ofPlatform().name("io-", 1).factory())) {
            CompletableFuture<BigDecimal> usd;
            if (chain) {
                // the rate call starts only when the price has arrived
                usd = CompletableFuture.supplyAsync(CombineDemo::priceEur, io)
                        .thenCompose(p -> CompletableFuture.supplyAsync(CombineDemo::eurToUsd, io)
                                .thenApply(p::multiply));
            } else {
                // both calls start now and run side by side
                CompletableFuture<BigDecimal> price = CompletableFuture.supplyAsync(CombineDemo::priceEur, io);
                CompletableFuture<BigDecimal> rate = CompletableFuture.supplyAsync(CombineDemo::eurToUsd, io);
                usd = price.thenCombine(rate, BigDecimal::multiply);
            }
            log("pipeline built, nothing has arrived yet");
            log("charge " + usd.join().setScale(2, RoundingMode.HALF_EVEN) + " USD");
        }
    }

    static void sleep(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }
}
