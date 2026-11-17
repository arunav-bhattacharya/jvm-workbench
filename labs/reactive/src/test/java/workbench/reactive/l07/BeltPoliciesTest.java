package workbench.reactive.l07;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.Exceptions;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.test.publisher.TestPublisher;

import java.time.Duration;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

class BeltPoliciesTest {

    @Test
    @DisplayName("nightlyReport delivers all 1,000 rows but never asks the database for more than 100 at a time")
    void reportCapsEachRequest() {
        List<Long> requests = new CopyOnWriteArrayList<>();
        Flux<Integer> orderRows = Flux.range(1, 1_000).doOnRequest(requests::add);

        StepVerifier.create(BeltPolicies.nightlyReport(orderRows))   // StepVerifier requests everything
                .expectNextCount(1_000)
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(requests).as("requests the database received").isNotEmpty();
        assertThat(requests.get(0)).as("first request").isEqualTo(100L);
        assertThat(requests).as("every request").allSatisfy(n -> assertThat(n).isLessThanOrEqualTo(100L));
    }

    @Test
    @DisplayName("latestTemperature gives a slow screen the newest reading, not the oldest and not the next one")
    void latestReadingWins() {
        TestPublisher<String> readings = TestPublisher.create();   // a well-behaved hot source: it fails if pushed without demand

        StepVerifier.create(BeltPolicies.latestTemperature(readings.flux()), 0)   // the screen asks for nothing yet
                .expectSubscription()
                .then(() -> readings.next("201", "202", "203", "204"))
                .thenRequest(1)
                .expectNext("204")
                .then(() -> readings.next("205"))
                .thenRequest(1)
                .expectNext("205")
                .thenCancel()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("webOrders holds 1,000 orders for a subscriber that is not asking, and loses none")
    void webOrdersHoldsAThousand() {
        TestPublisher<Integer> orders = TestPublisher.create();

        StepVerifier.create(BeltPolicies.webOrders(orders.flux()), 0)
                .expectSubscription()
                .then(() -> { for (int i = 1; i <= 1_000; i++) orders.next(i); })
                .thenRequest(1_000)
                .expectNextCount(1_000)
                .then(orders::complete)
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("webOrders fails loudly with an overflow error on the 1,001st waiting order, after delivering the 1,000")
    void webOrdersOverflowIsLoud() {
        TestPublisher<Integer> orders = TestPublisher.create();

        StepVerifier.create(BeltPolicies.webOrders(orders.flux()), 0)
                .expectSubscription()
                .then(() -> { for (int i = 1; i <= 1_001; i++) orders.next(i); })
                .thenRequest(1_000)
                .expectNextCount(1_000)
                .expectErrorSatisfies(e -> assertThat(Exceptions.isOverflow(e)).as("is an overflow error: " + e).isTrue())
                .verify(Duration.ofSeconds(5));

        orders.assertCancelled();                                    // the source is told to stop
    }

    @Test
    @DisplayName("bookCouriers never has more than 20 courier calls in flight, and books all 100 deliveries")
    void bookCouriersKeepsTwentyInFlight() {
        AtomicInteger inFlight = new AtomicInteger();
        AtomicInteger maxInFlight = new AtomicInteger();

        StepVerifier.withVirtualTime(() -> BeltPolicies.bookCouriers(Flux.range(1, 100), (Integer id) ->
                        Mono.defer(() -> {
                            maxInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                            return Mono.delay(Duration.ofMillis(50))                    // 50 ms of virtual time
                                    .map(tick -> {
                                        inFlight.decrementAndGet();                     // done before the result moves on
                                        return "van-" + id;
                                    });
                        })))
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(10))
                .expectNextCount(100)
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(maxInFlight).as("most courier calls in flight at once").hasValue(20);
    }
}
