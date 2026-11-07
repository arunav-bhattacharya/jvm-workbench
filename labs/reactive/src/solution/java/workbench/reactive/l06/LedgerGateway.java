package workbench.reactive.l06;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

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

    public Mono<BigDecimal> balance(String account) {
        return Mono.fromCallable(() -> ledger.balance(account))      // lazy: runs per subscription
                .subscribeOn(Schedulers.boundedElastic());          // and on a thread that may block
    }

    public Flux<BigDecimal> balances(List<String> accounts) {
        // each inner balance() carries its own subscribeOn, so the 4 calls really run at once;
        // flatMapSequential keeps the input order, and 4 caps how many inners are subscribed
        return Flux.fromIterable(accounts).flatMapSequential(this::balance, 4);
    }

    public Mono<BigDecimal> toEur(Mono<BigDecimal> usd) {
        // compose the second async call instead of waiting for it
        return usd.flatMap(amount -> fx.usdToEur().map(amount::multiply));
    }
}
