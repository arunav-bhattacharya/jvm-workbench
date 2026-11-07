package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.util.List;

/** A reactive front for a blocking ledger and a non-blocking FX client. */
public class LedgerGateway {
    private final BlockingLedger ledger;
    private final FxRates fx;

    public LedgerGateway(BlockingLedger ledger, FxRates fx) {
        this.ledger = ledger;
        this.fx = fx;
    }

    /**
     * The balance of one account. The blocking ledger call must run on {@code Schedulers.boundedElastic()},
     * never on the subscriber's thread, and only when the Mono is subscribed.
     */
    public Mono<BigDecimal> balance(String account) {
        throw new UnsupportedOperationException("TODO: wrap the blocking call");
    }

    /**
     * The balances of all the accounts, in the same order as {@code accounts}, with at most
     * 4 ledger calls running at the same time (the ledger's connection pool is small).
     */
    public Flux<BigDecimal> balances(List<String> accounts) {
        throw new UnsupportedOperationException("TODO: at most 4 at a time, in order");
    }

    /**
     * Converts a USD amount to EUR with the current rate.
     * BUG: this fails with an IllegalStateException when {@code usd} emits on a Reactor parallel thread,
     * which is where timers, timeouts and many clients deliver their results. Fix it without block().
     */
    public Mono<BigDecimal> toEur(Mono<BigDecimal> usd) {
        return usd.map(amount -> amount.multiply(fx.usdToEur().block()));
    }
}
