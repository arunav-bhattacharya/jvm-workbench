package workbench.reactive.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;

public final class OrderPage {
    private OrderPage() {}

    public static Mono<Quote> quote(Mono<BigDecimal> price, Mono<BigDecimal> deliveryFee, Mono<BigDecimal> taxRate) {
        // Mono.zip subscribes to all three at once. On its own, an empty source makes the whole
        // zip complete EMPTY (and cancels the others), so turn "empty" into an error first.
        return Mono.zip(
                        price.switchIfEmpty(missing("price")),
                        deliveryFee.switchIfEmpty(missing("delivery fee")),
                        taxRate.switchIfEmpty(missing("tax rate")))
                .map(t -> new Quote(t.getT1(), t.getT2(), t.getT3()));
    }

    private static <T> Mono<T> missing(String what) {
        return Mono.error(() -> new IllegalStateException("missing " + what));
    }

    public static Flux<String> kitchenScreen(Flux<String> counterOrders, Flux<String> webOrders) {
        // merge: subscribes to both at once and passes items on as they arrive
        return Flux.merge(counterOrders, webOrders);
    }

    public static Flux<String> daySheet(Flux<String> collected, Flux<String> waiting) {
        // concat: subscribes to waiting only after collected has completed
        return Flux.concat(collected, waiting);
    }

    public static Flux<BigDecimal> cakePrice(Flux<BigDecimal> weightsInKg, Flux<BigDecimal> pricesPerKg) {
        // combineLatest: after both have emitted once, every new value from either side
        // is combined with the latest value from the other
        return Flux.combineLatest(weightsInKg, pricesPerKg, BigDecimal::multiply);
    }
}
