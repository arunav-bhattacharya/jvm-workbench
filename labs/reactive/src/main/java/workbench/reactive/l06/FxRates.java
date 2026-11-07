package workbench.reactive.l06;

import reactor.core.publisher.Mono;

import java.math.BigDecimal;

/** A non-blocking FX client. Its Mono emits later, on a Reactor thread. */
public interface FxRates {
    Mono<BigDecimal> usdToEur();
}
