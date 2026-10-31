package workbench.reactive.l03;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

class PaymentFlowsTest {

    /** Wraps fake service calls so the tests can see how many run at once, and which were cancelled. */
    static final class Tracker {
        final AtomicInteger started = new AtomicInteger();
        final AtomicInteger inFlight = new AtomicInteger();
        final AtomicInteger maxInFlight = new AtomicInteger();
        final AtomicInteger cancelled = new AtomicInteger();

        Mono<String> call(String result, long millis) {
            return Mono.defer(() -> {
                AtomicBoolean finished = new AtomicBoolean();      // a cancel after completion doesn't count
                return Mono.delay(Duration.ofMillis(millis))
                        .thenReturn(result)
                        .doOnSubscribe(s -> {
                            started.incrementAndGet();
                            maxInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                        })
                        // doOnTerminate runs before the result goes downstream, so the next call can't start first
                        .doOnTerminate(() -> {
                            if (finished.compareAndSet(false, true)) inFlight.decrementAndGet();
                        })
                        .doOnCancel(() -> {
                            if (finished.compareAndSet(false, true)) {
                                inFlight.decrementAndGet();
                                cancelled.incrementAndGet();
                            }
                        });
            });
        }
    }

    @Test
    @DisplayName("fraudScores: scores all 12 payments with exactly 4 calls in flight at most")
    void fraudScoresUseFourSlots() {
        Tracker fraud = new Tracker();
        List<String> expected = new ArrayList<>();
        for (int i = 1; i <= 12; i++) expected.add("p-" + i + ":low");

        StepVerifier.withVirtualTime(() -> PaymentFlows.fraudScores(
                        Flux.range(1, 12).map(i -> "p-" + i),
                        id -> fraud.call(id + ":low", 50L * (1 + Integer.parseInt(id.substring(2)) % 3))))
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(10))
                .recordWith(ArrayList::new)
                .expectNextCount(12)
                .consumeRecordedWith(scores -> assertThat(scores).containsExactlyInAnyOrderElementsOf(expected))
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(fraud.maxInFlight).as("max fraud calls in flight").hasValue(4);
    }

    @Test
    @DisplayName("postAll: posts strictly one at a time, and results keep posting order")
    void postAllInOrder() {
        Tracker ledger = new Tracker();
        // the first posting is the slowest, so anything concurrent would finish out of order
        StepVerifier.withVirtualTime(() -> PaymentFlows.postAll(
                        Flux.just("debit-300", "credit-100", "debit-200", "fee-50"),
                        posting -> ledger.call("ok:" + posting, Long.parseLong(posting.substring(posting.indexOf('-') + 1)))))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(299))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("ok:debit-300")
                .thenAwait(Duration.ofMillis(100))
                .expectNext("ok:credit-100")
                .thenAwait(Duration.ofMillis(200))
                .expectNext("ok:debit-200")
                .thenAwait(Duration.ofMillis(50))
                .expectNext("ok:fee-50")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(ledger.maxInFlight).as("max postings in flight").hasValue(1);
    }

    @Test
    @DisplayName("postAll: after a failed posting, later postings are never sent")
    void postAllStopsAtFailure() {
        Tracker ledger = new Tracker();
        StepVerifier.withVirtualTime(() -> PaymentFlows.postAll(
                        Flux.just("debit-1", "debit-2", "debit-3"),
                        posting -> posting.equals("debit-2")
                                ? ledger.call("x", 10).then(Mono.error(new IllegalStateException("insufficient funds")))
                                : ledger.call("ok:" + posting, 10)))
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(1))
                .expectNext("ok:debit-1")
                .expectErrorMessage("insufficient funds")
                .verify(Duration.ofSeconds(5));

        assertThat(ledger.started).as("postings sent").hasValue(2);
    }

    @Test
    @DisplayName("latestQuotes: a newer pick cancels the quote still in flight for the older one")
    void latestQuoteWins() {
        Tracker fx = new Tracker();
        // picks at 0 ms (EUR), 50 ms (GBP) and 300 ms (JPY); each quote takes 100 ms
        StepVerifier.withVirtualTime(() -> PaymentFlows.latestQuotes(
                        Flux.concat(
                                Mono.just("EUR"),
                                Mono.just("GBP").delayElement(Duration.ofMillis(50)),
                                Mono.just("JPY").delayElement(Duration.ofMillis(250))),
                        ccy -> fx.call(ccy + "=quote", 100)))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(149))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("GBP=quote")                      // at 150 ms; EUR was abandoned at 50 ms
                .thenAwait(Duration.ofMillis(250))
                .expectNext("JPY=quote")                      // at 400 ms
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(fx.cancelled).as("quotes cancelled").hasValue(1);
    }
}
