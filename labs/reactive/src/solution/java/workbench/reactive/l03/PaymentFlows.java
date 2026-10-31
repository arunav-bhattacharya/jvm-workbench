package workbench.reactive.l03;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

public final class PaymentFlows {
    private PaymentFlows() {}

    public static Flux<String> fraudScores(Flux<String> paymentIds, Function<String, Mono<String>> fraudService) {
        // flatMap: subscribes to inners eagerly and merges results as they finish.
        // The concurrency argument caps how many inners are subscribed at once (default 256).
        return paymentIds.flatMap(fraudService, 4);
    }

    public static Flux<String> postAll(Flux<String> postings, Function<String, Mono<String>> ledger) {
        // concatMap: subscribes to the next inner only after the previous one completes.
        // An inner error ends the stream, so later postings are never subscribed (never sent).
        return postings.concatMap(ledger);
    }

    public static Flux<String> latestQuotes(Flux<String> currencyPicks, Function<String, Mono<String>> fxService) {
        // switchMap: each new pick cancels the inner for the previous pick.
        // (switchMap wants a Function returning Publisher exactly, so pass a lambda, not fxService itself)
        return currencyPicks.switchMap(ccy -> fxService.apply(ccy));
    }
}
