package workbench.reactive.l04;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.test.publisher.PublisherProbe;
import reactor.test.publisher.TestPublisher;

import java.math.BigDecimal;
import java.time.Duration;

import static org.assertj.core.api.Assertions.assertThat;

class CheckoutTest {
    private static Mono<BigDecimal> after(long millis, String value) {
        return Mono.delay(Duration.ofMillis(millis)).thenReturn(new BigDecimal(value));
    }

    private static boolean same(BigDecimal actual, String expected) {
        return actual.compareTo(new BigDecimal(expected)) == 0;
    }

    @Test
    @DisplayName("quote: runs the three lookups at once, so it is ready after the slowest (300 ms), not the sum")
    void quoteRunsConcurrently() {
        StepVerifier.withVirtualTime(() -> Checkout.quote(after(100, "1.08"), after(300, "0.30"), after(200, "500")))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(299))
                .thenAwait(Duration.ofMillis(1))
                .assertNext(q -> {
                    assertThat(q.fxRate()).isEqualByComparingTo("1.08");
                    assertThat(q.fee()).isEqualByComparingTo("0.30");
                    assertThat(q.limit()).isEqualByComparingTo("500");
                })
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("quote: an empty lookup is an error naming what is missing, never an empty result")
    void quoteFailsOnEmpty() {
        StepVerifier.withVirtualTime(() -> Checkout.quote(after(100, "1.08"), Mono.empty(), after(200, "500")))
                .expectSubscription()
                .expectErrorSatisfies(e -> assertThat(e)
                        .isInstanceOf(IllegalStateException.class)
                        .hasMessage("missing fee"))
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("activityFeed: card and bank events are interleaved in the order they happen")
    void feedInterleaves() {
        StepVerifier.withVirtualTime(() -> Checkout.activityFeed(
                        Flux.just("card-1", "card-2").delayElements(Duration.ofMillis(20)),          // 20, 40 ms
                        Flux.just("bank-1", "bank-2").delayElements(Duration.ofMillis(30))))         // 30, 60 ms
                .expectSubscription()
                .thenAwait(Duration.ofMillis(100))
                .expectNext("card-1", "bank-1", "card-2", "bank-2")
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("statement: settled entries first; pending is not subscribed until settled completes")
    void statementIsSequential() {
        TestPublisher<String> settled = TestPublisher.create();
        PublisherProbe<String> pending = PublisherProbe.of(Flux.just("pending-1", "pending-2"));

        StepVerifier.create(Checkout.statement(settled.flux(), pending.flux()))
                .then(() -> settled.next("settled-1", "settled-2"))
                .expectNext("settled-1", "settled-2")
                .then(pending::assertWasNotSubscribed)
                .then(settled::complete)
                .expectNext("pending-1", "pending-2")
                .expectComplete()
                .verify(Duration.ofSeconds(5));
        pending.assertWasSubscribed();
    }

    @Test
    @DisplayName("limitInUsd: recomputes when either the limit or the rate changes")
    void limitFollowsBothInputs() {
        StepVerifier.withVirtualTime(() -> Checkout.limitInUsd(
                        Flux.concat(after(0, "1000"), after(30, "2000")),                  // limit at 0 and 30 ms
                        Flux.concat(after(10, "1.10"), after(10, "1.20"))))                // rate at 10 and 20 ms
                .expectSubscription()
                .thenAwait(Duration.ofMillis(100))
                .expectNextMatches(v -> same(v, "1100"))     // 1000 x 1.10, at 10 ms
                .expectNextMatches(v -> same(v, "1200"))     // 1000 x 1.20, at 20 ms
                .expectNextMatches(v -> same(v, "2400"))     // 2000 x 1.20, at 30 ms
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }
}
