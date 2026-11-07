package workbench.reactive.l08;

import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;
import reactor.test.publisher.TestPublisher;

import java.time.Duration;
import java.util.concurrent.atomic.AtomicInteger;

/** Five StepVerifier habits, most of them shown by breaking them. */
public class StepVerifierDemo {
    public static void main(String[] args) {
        AtomicInteger subscriptions = new AtomicInteger();
        Mono<String> charge = Mono.fromCallable(() -> "charged").doOnSubscribe(s -> subscriptions.incrementAndGet());
        StepVerifier.create(charge).expectNext("refunded").expectComplete();          // no verify(): nothing runs
        System.out.println("1. no verify():     subscriptions=" + subscriptions.get() + ", wrong expectation unnoticed");

        Duration real = StepVerifier.withVirtualTime(() -> Mono.delay(Duration.ofDays(1)).thenReturn("expired"))
                .expectSubscription()
                .expectNoEvent(Duration.ofDays(1))
                .expectNext("expired")
                .verifyComplete();
        System.out.println("2. virtual time:    one day took " + real.toMillis() + " ms of real time");

        try {
            StepVerifier.withVirtualTime(() -> Mono.delay(Duration.ofDays(1)))
                    .expectNoEvent(Duration.ofDays(1))                                 // subscription counts as an event
                    .expectNext(0L)
                    .verifyComplete();
        } catch (AssertionError e) {
            System.out.println("3. expectNoEvent first: " + e.getMessage());
        }

        Mono<String> builtTooEarly = Mono.delay(Duration.ofDays(1)).thenReturn("expired");  // grabs the real clock
        try {
            StepVerifier.withVirtualTime(() -> builtTooEarly)
                    .expectSubscription()
                    .thenAwait(Duration.ofDays(1))
                    .expectNext("expired")
                    .expectComplete()
                    .verify(Duration.ofSeconds(1));
        } catch (AssertionError e) {
            System.out.println("4. built outside the supplier: " + e.getMessage());
        }

        TestPublisher<String> rates = TestPublisher.create();
        StepVerifier.create(rates.flux().map(r -> "EUR/USD " + r))
                .then(() -> rates.next("1.08", "1.09"))                                // push values by hand
                .expectNext("EUR/USD 1.08", "EUR/USD 1.09")
                .then(rates::complete)
                .expectComplete()
                .verify(Duration.ofSeconds(1));
        System.out.println("5. TestPublisher:   passed; the map requested " + (rates.wasRequested() ? "some" : "no") + " items");
    }
}
