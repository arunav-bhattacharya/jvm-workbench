package workbench.executors.l07;

import java.math.BigDecimal;
import java.util.Comparator;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/** flaky fails at 50 ms, alpha answers at 100 ms, beta at 300 ms. Pass any, all or safe. */
public class FanOutDemo {
    static final long T0 = System.nanoTime();

    static void log(String msg) {
        System.out.printf("%4d ms  %s%n", (System.nanoTime() - T0) / 1_000_000, msg);
    }

    static CompletableFuture<BigDecimal> ask(String name, long ms, String price, ExecutorService io) {
        return CompletableFuture.supplyAsync(() -> {
            sleep(ms);
            if (price == null) {
                log(name + " fails");
                throw new IllegalStateException(name + " returned 503");
            }
            log(name + " answers " + price);
            return new BigDecimal(price);
        }, io);
    }

    public static void main(String[] args) {
        String mode = args.length > 0 ? args[0] : "all";
        try (ExecutorService io = Executors.newFixedThreadPool(3, Thread.ofPlatform().name("io-", 1).factory())) {
            List<CompletableFuture<BigDecimal>> asks = List.of(
                    ask("flaky", 50, null, io), ask("alpha", 100, "1.0850", io), ask("beta", 300, "1.0842", io));
            CompletableFuture<?> result = switch (mode) {
                // the first future to complete wins, even when it completes with a failure
                case "any" -> CompletableFuture.anyOf(asks.toArray(CompletableFuture[]::new));
                // waits for all three, then fails because one of them failed
                case "all" -> CompletableFuture.allOf(asks.toArray(CompletableFuture[]::new))
                        .thenApply(done -> asks.stream().map(CompletableFuture::join).min(Comparator.naturalOrder()).orElseThrow());
                // turn each failure into an empty Optional first, so allOf can't fail
                default -> {
                    List<CompletableFuture<Optional<BigDecimal>>> safe = asks.stream()
                            .map(f -> f.handle((price, ex) -> ex == null ? Optional.of(price) : Optional.<BigDecimal>empty()))
                            .toList();
                    yield CompletableFuture.allOf(safe.toArray(CompletableFuture[]::new))
                            .thenApply(done -> safe.stream().map(CompletableFuture::join).flatMap(Optional::stream)
                                    .min(Comparator.naturalOrder()).orElseThrow());
                }
            };
            result.handle((v, ex) -> {
                log(mode + ": " + (ex == null ? "result " + v : "failed with " + ex.getCause()));
                return null;
            }).join();
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
