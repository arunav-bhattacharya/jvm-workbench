package workbench.reactive.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;

public final class Checkout {
    private Checkout() {}

    public static Mono<Quote> quote(Mono<BigDecimal> fxRate, Mono<BigDecimal> fee, Mono<BigDecimal> limit) {
        // Mono.zip subscribes to all three at once. On its own, an empty source makes the whole
        // zip complete EMPTY (and cancels the others), so turn "empty" into an error first.
        return Mono.zip(
                        fxRate.switchIfEmpty(missing("fx rate")),
                        fee.switchIfEmpty(missing("fee")),
                        limit.switchIfEmpty(missing("limit")))
                .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));
    }

    private static <T> Mono<T> missing(String what) {
        return Mono.error(() -> new IllegalStateException("missing " + what));
    }

    public static Flux<String> activityFeed(Flux<String> cardEvents, Flux<String> bankEvents) {
        // merge: subscribes to both at once and passes items on as they arrive
        return Flux.merge(cardEvents, bankEvents);
    }

    public static Flux<String> statement(Flux<String> settled, Flux<String> pending) {
        // concat: subscribes to pending only after settled has completed
        return Flux.concat(settled, pending);
    }

    public static Flux<BigDecimal> limitInUsd(Flux<BigDecimal> limitsInEur, Flux<BigDecimal> eurUsdRates) {
        // combineLatest: after both have emitted once, every new value from either side
        // is combined with the latest value from the other
        return Flux.combineLatest(limitsInEur, eurUsdRates, BigDecimal::multiply);
    }
}
