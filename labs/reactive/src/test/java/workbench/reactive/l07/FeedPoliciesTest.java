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

class FeedPoliciesTest {

    @Test
    @DisplayName("ledgerExport delivers all 1,000 rows but never asks the cursor for more than 100 at a time")
    void exportCapsEachRequest() {
        List<Long> requests = new CopyOnWriteArrayList<>();
        Flux<Integer> cursor = Flux.range(1, 1_000).doOnRequest(requests::add);

        StepVerifier.create(FeedPolicies.ledgerExport(cursor))      // StepVerifier requests everything
                .expectNextCount(1_000)
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(requests).as("requests the cursor received").isNotEmpty();
        assertThat(requests.get(0)).as("first request").isEqualTo(100L);
        assertThat(requests).as("every request").allSatisfy(n -> assertThat(n).isLessThanOrEqualTo(100L));
    }

    @Test
    @DisplayName("latestTicks gives a slow screen the newest tick, not the oldest and not the next one")
    void latestTickWins() {
        TestPublisher<String> ticks = TestPublisher.create();      // a well-behaved hot feed: it fails if pushed without demand

        StepVerifier.create(FeedPolicies.latestTicks(ticks.flux()), 0)   // the screen asks for nothing yet
                .expectSubscription()
                .then(() -> ticks.next("1.0811", "1.0812", "1.0813", "1.0814"))
                .thenRequest(1)
                .expectNext("1.0814")
                .then(() -> ticks.next("1.0815"))
                .thenRequest(1)
                .expectNext("1.0815")
                .thenCancel()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("auditEvents holds 1,000 events for a subscriber that is not asking, and loses none")
    void auditHoldsAThousand() {
        TestPublisher<Integer> events = TestPublisher.create();

        StepVerifier.create(FeedPolicies.auditEvents(events.flux()), 0)
                .expectSubscription()
                .then(() -> { for (int i = 1; i <= 1_000; i++) events.next(i); })
                .thenRequest(1_000)
                .expectNextCount(1_000)
                .then(events::complete)
                .expectComplete()
                .verify(Duration.ofSeconds(5));
    }

    @Test
    @DisplayName("auditEvents fails loudly with an overflow error on the 1,001st waiting event, after delivering the 1,000")
    void auditOverflowIsLoud() {
        TestPublisher<Integer> events = TestPublisher.create();

        StepVerifier.create(FeedPolicies.auditEvents(events.flux()), 0)
                .expectSubscription()
                .then(() -> { for (int i = 1; i <= 1_001; i++) events.next(i); })
                .thenRequest(1_000)
                .expectNextCount(1_000)
                .expectErrorSatisfies(e -> assertThat(Exceptions.isOverflow(e)).as("is an overflow error: " + e).isTrue())
                .verify(Duration.ofSeconds(5));

        events.assertCancelled();                                    // the source is told to stop
    }

    @Test
    @DisplayName("settle never has more than 20 bank calls in flight, and settles all 100 payments")
    void settleKeepsTwentyInFlight() {
        AtomicInteger inFlight = new AtomicInteger();
        AtomicInteger maxInFlight = new AtomicInteger();

        StepVerifier.withVirtualTime(() -> FeedPolicies.settle(Flux.range(1, 100), (Integer id) ->
                        Mono.defer(() -> {
                            maxInFlight.accumulateAndGet(inFlight.incrementAndGet(), Math::max);
                            return Mono.delay(Duration.ofMillis(50))                    // 50 ms of virtual time
                                    .map(tick -> {
                                        inFlight.decrementAndGet();                     // done before the result moves on
                                        return "receipt-" + id;
                                    });
                        })))
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(10))
                .expectNextCount(100)
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(maxInFlight).as("most bank calls in flight at once").hasValue(20);
    }
}
