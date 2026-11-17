package workbench.reactive.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;

/**
 * Four ways to combine streams for the bakery's order page and kitchen. Each method is one or two
 * lines once you pick the right combinator: {@code zip}, {@code merge}, {@code concat} or {@code combineLatest}.
 */
public final class OrderPage {
    private OrderPage() {}

    /**
     * Builds a quote from three lookups that must run at the same time, not one after another.
     * If any lookup comes back empty, fail with {@code IllegalStateException("missing <name>")},
     * where name is "price", "delivery fee" or "tax rate". Never complete empty.
     */
    public static Mono<Quote> quote(Mono<BigDecimal> price, Mono<BigDecimal> deliveryFee, Mono<BigDecimal> taxRate) {
        throw new UnsupportedOperationException("TODO: run all three at once and build a Quote");
    }

    /**
     * Orders from the shop counter and from the website, shown on the kitchen screen in the order
     * they arrive, from both sources at once.
     */
    public static Flux<String> kitchenScreen(Flux<String> counterOrders, Flux<String> webOrders) {
        throw new UnsupportedOperationException("TODO: interleave by arrival time");
    }

    /**
     * The end-of-day sheet: all collected orders first, then the ones still waiting. The waiting
     * source is a slow search, so it must not even be subscribed until the collected orders are complete.
     */
    public static Flux<String> daySheet(Flux<String> collected, Flux<String> waiting) {
        throw new UnsupportedOperationException("TODO: collected, then waiting");
    }

    /**
     * The price shown on the order page: the cake's weight in kilograms times the latest price per kilogram.
     * Emit a new value whenever either the weight or the price changes (once both are known).
     */
    public static Flux<BigDecimal> cakePrice(Flux<BigDecimal> weightsInKg, Flux<BigDecimal> pricesPerKg) {
        throw new UnsupportedOperationException("TODO: recompute on every change of either input");
    }
}
