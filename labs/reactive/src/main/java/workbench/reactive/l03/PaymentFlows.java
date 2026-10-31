package workbench.reactive.l03;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

/**
 * Three pipelines, three different needs. Each body is one line: pick the operator that fits.
 * Choose between {@code flatMap} (with or without a concurrency argument), {@code concatMap},
 * {@code flatMapSequential} and {@code switchMap}.
 */
public final class PaymentFlows {
    private PaymentFlows() {}

    /**
     * Scores every payment with the fraud service. Results may come back in any order.
     * The fraud service allows at most 4 concurrent calls from us, and we want to use all 4.
     */
    public static Flux<String> fraudScores(Flux<String> paymentIds, Function<String, Mono<String>> fraudService) {
        throw new UnsupportedOperationException("TODO: any order, at most 4 calls in flight");
    }

    /**
     * Posts entries to one account's ledger. Each posting must be acknowledged before the next one
     * is sent (the ledger checks the balance), results come back in posting order, and after a
     * failed posting no later posting may be sent.
     */
    public static Flux<String> postAll(Flux<String> postings, Function<String, Mono<String>> ledger) {
        throw new UnsupportedOperationException("TODO: strictly one at a time, in order");
    }

    /**
     * The user picks currencies in a dropdown; each pick asks the FX service for a quote.
     * Only the quote for the most recent pick matters: a quote still in flight when the user
     * picks again must be abandoned (cancelled), and must never be shown.
     */
    public static Flux<String> latestQuotes(Flux<String> currencyPicks, Function<String, Mono<String>> fxService) {
        throw new UnsupportedOperationException("TODO: only the latest pick counts");
    }
}
