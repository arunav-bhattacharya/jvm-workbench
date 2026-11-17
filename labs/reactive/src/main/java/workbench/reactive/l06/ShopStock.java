package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.util.List;

/** A reactive front for the bakery's blocking stock book and its non-blocking price list. */
public class ShopStock {
    private final StockBook stock;
    private final PriceList prices;

    public ShopStock(StockBook stock, PriceList prices) {
        this.stock = stock;
        this.prices = prices;
    }

    /**
     * The loaves one shop has left. The blocking stock-book call must run on {@code Schedulers.boundedElastic()},
     * never on the subscriber's thread, and only when the Mono is subscribed.
     */
    public Mono<Integer> loavesLeft(String shop) {
        throw new UnsupportedOperationException("TODO: wrap the blocking call");
    }

    /**
     * The loaves left in every shop, in the same order as {@code shops}, with at most
     * 4 stock-book calls running at the same time (the stock database allows only a few connections).
     */
    public Flux<Integer> loavesLeftIn(List<String> shops) {
        throw new UnsupportedOperationException("TODO: at most 4 at a time, in order");
    }

    /**
     * What a number of loaves is worth at the current price per loaf.
     * BUG: this fails with an IllegalStateException when {@code loaves} emits on a Reactor parallel thread,
     * which is where timers, timeouts and many clients deliver their results. Fix it without block().
     */
    public Mono<BigDecimal> stockValue(Mono<Integer> loaves) {
        return loaves.map(n -> prices.pricePerLoaf().block().multiply(BigDecimal.valueOf(n)));
    }
}
