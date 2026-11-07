package workbench.reactive.l07;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

/**
 * Four feeds, four backpressure decisions. Each method is one or two operators.
 * Decide which one before you type: does the source honour request(n)? May anything be lost?
 */
public final class FeedPolicies {
    private FeedPolicies() {
    }

    /**
     * A nightly export reads ledger rows from a database cursor that fetches as many rows as it is asked for.
     * The HTTP uploader downstream asks for everything at once. Keep every row, but never ask the cursor
     * for more than 100 rows at a time.
     */
    public static <T> Flux<T> ledgerExport(Flux<T> cursorRows) {
        throw new UnsupportedOperationException("TODO: cap each upstream request at 100");
    }

    /**
     * A live FX tick feed that cannot slow down. The pricing screen is slow and only ever needs the
     * newest tick: when it asks for one, give it the most recent tick and forget the older ones.
     */
    public static <T> Flux<T> latestTicks(Flux<T> ticks) {
        throw new UnsupportedOperationException("TODO: keep only the newest tick");
    }

    /**
     * Audit events from a source that cannot slow down. None may be lost silently. Hold up to 1,000
     * events for a slow subscriber; if a 1,001st has to wait, fail the stream with an overflow error
     * (after the subscriber has received the 1,000 that were held) so the gap is visible.
     */
    public static <T> Flux<T> auditEvents(Flux<T> events) {
        throw new UnsupportedOperationException("TODO: bounded buffer, loud overflow");
    }

    /**
     * Settles every payment through the bank's API. The bank allows 20 open requests per client;
     * never have more than 20 calls in flight. The order of the results does not matter.
     */
    public static <T, R> Flux<R> settle(Flux<T> payments, Function<T, Mono<R>> bankCall) {
        throw new UnsupportedOperationException("TODO: at most 20 calls in flight");
    }
}
