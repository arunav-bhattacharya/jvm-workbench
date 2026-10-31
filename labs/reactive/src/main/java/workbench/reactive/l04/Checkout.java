package workbench.reactive.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;

/**
 * Four ways to combine streams on a checkout page. Each method is one or two lines once you
 * pick the right combinator: {@code zip}, {@code merge}, {@code concat} or {@code combineLatest}.
 */
public final class Checkout {
    private Checkout() {}

    /**
     * Builds a quote from three lookups that must run at the same time, not one after another.
     * If any lookup comes back empty, fail with {@code IllegalStateException("missing <name>")},
     * where name is "fx rate", "fee" or "limit". Never complete empty.
     */
    public static Mono<Quote> quote(Mono<BigDecimal> fxRate, Mono<BigDecimal> fee, Mono<BigDecimal> limit) {
        throw new UnsupportedOperationException("TODO: run all three at once and build a Quote");
    }

    /**
     * Card and bank events for the live activity feed, shown in the order they happen,
     * from both sources at once.
     */
    public static Flux<String> activityFeed(Flux<String> cardEvents, Flux<String> bankEvents) {
        throw new UnsupportedOperationException("TODO: interleave by arrival time");
    }

    /**
     * A statement: all settled entries first, then the pending ones. The pending source is an
     * expensive query, so it must not even be subscribed until the settled entries are complete.
     */
    public static Flux<String> statement(Flux<String> settled, Flux<String> pending) {
        throw new UnsupportedOperationException("TODO: settled, then pending");
    }

    /**
     * The customer's spending limit in USD: limit in EUR times the latest EUR/USD rate.
     * Emit a new value whenever either the limit or the rate changes (once both are known).
     */
    public static Flux<BigDecimal> limitInUsd(Flux<BigDecimal> limitsInEur, Flux<BigDecimal> eurUsdRates) {
        throw new UnsupportedOperationException("TODO: recompute on every change of either input");
    }
}
