package workbench.flows.l08;

import static org.assertj.core.api.Assertions.assertThat;
import static org.junit.jupiter.api.Assertions.assertThrows;

import java.io.IOException;
import java.time.Duration;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import reactor.core.publisher.Sinks;
import reactor.test.StepVerifier;

// Java equivalent of TurbineTourTest: reactor-test's StepVerifier is Reactor's stenographer.
// Not part of the lab. Every test passes; read each one and predict before you run the class.
class StepVerifierTourTest {

    @Test
    @DisplayName("1. items and completion are expected in order")
    void itemsThenComplete() {
        StepVerifier.create(Flux.just("AUTHORIZED", "CAPTURED"))
                .expectNext("AUTHORIZED")
                .expectNext("CAPTURED")
                .expectComplete()
                .verify(Duration.ofSeconds(1));
    }

    @Test
    @DisplayName("2. a signal you did not expect fails the test")
    void unexpectedSignal() {
        AssertionError failure = assertThrows(AssertionError.class, () ->
                StepVerifier.create(Flux.just("one", "two")).expectNext("one").expectComplete().verify(Duration.ofSeconds(1)));
        assertThat(failure).hasMessageContaining("actual: onNext(two)");
    }

    @Test
    @DisplayName("3. an error is a signal you expect")
    void errorSignal() {
        StepVerifier.create(Flux.concat(Flux.just(1), Flux.error(new IOException("issuer 503"))))
                .expectNext(1)
                .expectErrorMessage("issuer 503")
                .verify(Duration.ofSeconds(1));
    }

    @Test
    @DisplayName("4. a Kotlin StateFlow through asFlux(): every value arrives, as with Turbine")
    void stateFlowAsFlux() {
        TourTracker tracker = new TourTracker();
        StepVerifier.create(tracker.statusFlux())
                .expectNext("PENDING")
                .then(tracker::authorizeAndCapture)
                .expectNext("AUTHORIZED", "CAPTURED")
                .thenCancel()
                .verify(Duration.ofSeconds(1));
    }

    @Test
    @DisplayName("5. a hot item emitted before anyone subscribed is gone")
    void hotBeforeSubscribe() {
        Sinks.Many<String> events = Sinks.many().multicast().directBestEffort();
        assertThat(events.tryEmitNext("AUTHORIZED")).isEqualTo(Sinks.EmitResult.FAIL_ZERO_SUBSCRIBER);
        AssertionError failure = assertThrows(AssertionError.class, () ->
                StepVerifier.create(events.asFlux()).expectNext("AUTHORIZED").thenCancel().verify(Duration.ofMillis(500)));
        assertThat(failure).hasMessageContaining("timed out");
    }

    @Test
    @DisplayName("6. virtual time: thenAwait(10 s) runs the task due at exactly +10 s")
    void virtualTime() {
        StepVerifier.withVirtualTime(() -> Mono.delay(Duration.ofSeconds(10)).map(tick -> "late"))
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(10))
                .expectNext("late")
                .expectComplete()
                .verify(Duration.ofSeconds(1));
    }
}
