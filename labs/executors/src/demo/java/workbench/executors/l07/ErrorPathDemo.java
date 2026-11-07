package workbench.executors.l07;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** The FX call fails. Which steps still run? Pass "early" to recover the rate right after the call. */
public class ErrorPathDemo {
    static BigDecimal liveRate() {
        throw new IllegalStateException("FX provider returned 502");
    }

    static <T> T step(String what, T value) {
        System.out.println(what);
        return value;
    }

    public static void main(String[] args) {
        boolean early = args.length > 0 && args[0].equals("early");
        try (ExecutorService io = Executors.newFixedThreadPool(1, Thread.ofPlatform().name("io-", 1).factory())) {
            CompletableFuture<BigDecimal> rate = CompletableFuture.supplyAsync(ErrorPathDemo::liveRate, io);
            if (early) {
                rate = rate.exceptionally(ex -> {                  // recover the rate itself
                    System.out.println("exceptionally sees: " + ex);
                    return new BigDecimal("1.0800");               // the last known rate
                });
            }
            CompletableFuture<String> result = rate
                    .thenApply(r -> step("1. convert at " + r, new BigDecimal("100.00").multiply(r)))
                    .thenApply(usd -> step("2. round to cents", usd.setScale(2, RoundingMode.HALF_EVEN)))
                    .thenApply(usd -> step("3. charge " + usd + " USD", "charged " + usd + " USD"))
                    .whenComplete((v, ex) -> System.out.println("whenComplete sees: " + (ex == null ? v : ex)));
            if (!early) {
                result = result.exceptionally(ex -> {              // recover at the end instead
                    System.out.println("exceptionally sees: " + ex);
                    return "declined: FX rate unavailable";
                });
            }
            System.out.println("result: " + result.join());
        }
    }
}
