package workbench.reactive.l07;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.function.Function;

public final class FeedPolicies {
    private FeedPolicies() {
    }

    public static <T> Flux<T> ledgerExport(Flux<T> cursorRows) {
        // turns one huge request from downstream into requests of 100, then 75 each time 75 have gone out
        return cursorRows.limitRate(100);
    }

    public static <T> Flux<T> latestTicks(Flux<T> ticks) {
        // requests unbounded from the feed and keeps one slot: the newest tick wins
        return ticks.onBackpressureLatest();
    }

    public static <T> Flux<T> auditEvents(Flux<T> events) {
        // parks up to 1,000; the next one cancels the source and ends the stream with an
        // OverflowException, delivered after the subscriber drains the buffer
        return events.onBackpressureBuffer(1_000);
    }

    public static <T, R> Flux<R> settle(Flux<T> payments, Function<T, Mono<R>> bankCall) {
        // flatMap subscribes to at most 20 inner calls, and asks the source for a new payment
        // only when one of them finishes
        return payments.flatMap(bankCall, 20);
    }
}
