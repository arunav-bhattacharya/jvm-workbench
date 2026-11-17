package workbench.reactive.l06;

import reactor.core.publisher.Mono;

import java.math.BigDecimal;

/** The bakery's price list, a non-blocking client. Its Mono emits later, on a Reactor thread. */
public interface PriceList {
    Mono<BigDecimal> pricePerLoaf();
}
