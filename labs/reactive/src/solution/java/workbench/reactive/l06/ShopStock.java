package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

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

    public Mono<Integer> loavesLeft(String shop) {
        return Mono.fromCallable(() -> stock.loavesLeft(shop))       // lazy: runs per subscription
                .subscribeOn(Schedulers.boundedElastic());          // and on a thread that may block
    }

    public Flux<Integer> loavesLeftIn(List<String> shops) {
        // each inner loavesLeft() carries its own subscribeOn, so the 4 calls really run at once;
        // flatMapSequential keeps the input order, and 4 caps how many inners are subscribed
        return Flux.fromIterable(shops).flatMapSequential(this::loavesLeft, 4);
    }

    public Mono<BigDecimal> stockValue(Mono<Integer> loaves) {
        // compose the second async call instead of waiting for it
        return loaves.flatMap(n -> prices.pricePerLoaf().map(price -> price.multiply(BigDecimal.valueOf(n))));
    }
}
