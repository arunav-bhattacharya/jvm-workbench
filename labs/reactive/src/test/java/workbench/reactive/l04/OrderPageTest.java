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

class OrderPageTest {
    private static Mono<BigDecimal> after(long millis, String value) {
        return Mono.delay(Duration.ofMillis(millis)).thenReturn(new BigDecimal(value));
    }

    private static boolean same(BigDecimal actual, String expected) {
        return actual.compareTo(new BigDecimal(expected)) == 0;
    }

    @Test
    @DisplayName("quote: runs the three lookups at once, so it is ready after the slowest (300 ms), not the sum")
    void quoteRunsConcurrently() {
        StepVerifier.withVirtualTime(() -> OrderPage.quote(after(100, "24.00"), after(300, "3.50"), after(200, "0.08")))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(299))
                .thenAwait(Duration.ofMillis(1))
                .assertNext(q -> {
                    assertThat(q.price()).isEqualByComparingTo("24.00");
                    assertThat(q.deliveryFee()).isEqualByComparingTo("3.50");
                    assertThat(q.taxRate()).isEqualByComparingTo("0.08");
                })
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("quote: an empty lookup is an error naming what is missing, never an empty result")
    void quoteFailsOnEmpty() {
        StepVerifier.withVirtualTime(() -> OrderPage.quote(after(100, "24.00"), Mono.empty(), after(200, "0.08")))
                .expectSubscription()
                .expectErrorSatisfies(e -> assertThat(e)
                        .isInstanceOf(IllegalStateException.class)
                        .hasMessage("missing delivery fee"))
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("kitchenScreen: counter and web orders are interleaved in the order they arrive")
    void screenInterleaves() {
        StepVerifier.withVirtualTime(() -> OrderPage.kitchenScreen(
                        Flux.just("counter-1", "counter-2").delayElements(Duration.ofMillis(20)),   // 20, 40 ms
                        Flux.just("web-1", "web-2").delayElements(Duration.ofMillis(30))))          // 30, 60 ms
                .expectSubscription()
                .thenAwait(Duration.ofMillis(100))
                .expectNext("counter-1", "web-1", "counter-2", "web-2")
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("daySheet: collected orders first; waiting is not subscribed until collected completes")
    void daySheetIsSequential() {
        TestPublisher<String> collected = TestPublisher.create();
        PublisherProbe<String> waiting = PublisherProbe.of(Flux.just("waiting-1", "waiting-2"));

        StepVerifier.create(OrderPage.daySheet(collected.flux(), waiting.flux()))
                .then(() -> collected.next("collected-1", "collected-2"))
                .expectNext("collected-1", "collected-2")
                .then(waiting::assertWasNotSubscribed)
                .then(collected::complete)
                .expectNext("waiting-1", "waiting-2")
                .expectComplete()
                .verify(Duration.ofSeconds(5));
        waiting.assertWasSubscribed();
    }

    @Test
    @DisplayName("cakePrice: recomputes when either the weight or the price per kilogram changes")
    void priceFollowsBothInputs() {
        StepVerifier.withVirtualTime(() -> OrderPage.cakePrice(
                        Flux.concat(after(0, "1.5"), after(30, "2.0")),                // weight at 0 and 30 ms
                        Flux.concat(after(10, "20.00"), after(10, "22.00"))))          // price at 10 and 20 ms
                .expectSubscription()
                .thenAwait(Duration.ofMillis(100))
                .expectNextMatches(v -> same(v, "30"))     // 1.5 kg x 20.00, at 10 ms
                .expectNextMatches(v -> same(v, "33"))     // 1.5 kg x 22.00, at 20 ms
                .expectNextMatches(v -> same(v, "44"))     // 2.0 kg x 22.00, at 30 ms
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }
}
