package workbench.reactive.l02;

import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import reactor.core.publisher.Mono;
import reactor.test.StepVerifier;

import java.util.List;
import java.util.concurrent.atomic.AtomicInteger;

import static org.assertj.core.api.Assertions.assertThat;

class LazinessTest {
    private final AtomicInteger calls = new AtomicInteger();

    private final IssuerApi issuer = paymentId -> {
        calls.incrementAndGet();
        if (paymentId.equals("boom")) throw new IllegalStateException("issuer down");
        if (paymentId.equals("unknown")) return null;
        return "SETTLED:" + paymentId;
    };

    @Test
    @DisplayName("status() makes no issuer call until someone subscribes")
    void noCallAtAssembly() {
        new PaymentLookup(issuer).status("p-1");
        assertThat(calls).as("issuer calls after building the Mono").hasValue(0);
    }

    @Test
    @DisplayName("status() calls the issuer once per subscription")
    void oneCallPerSubscription() {
        Mono<String> status = new PaymentLookup(issuer).status("p-1");
        assertThat(status.block()).isEqualTo("SETTLED:p-1");
        assertThat(status.block()).isEqualTo("SETTLED:p-1");
        assertThat(calls).as("issuer calls after two subscriptions").hasValue(2);
    }

    @Test
    @DisplayName("an issuer failure arrives as onError, not as an exception from status()")
    void failureIsASignal() {
        Mono<String> status = new PaymentLookup(issuer).status("boom");   // must not throw here
        StepVerifier.create(status)
                .expectErrorMessage("issuer down")
                .verify();
    }

    @Test
    @DisplayName("an unknown payment (issuer returns null) gives an empty Mono")
    void nullIsEmpty() {
        StepVerifier.create(new PaymentLookup(issuer).status("unknown"))
                .verifyComplete();
    }

    @Test
    @DisplayName("statuses() only calls the issuer for items the subscriber requests")
    void statusesAreLazy() {
        var lookup = new PaymentLookup(issuer);
        var all = lookup.statuses(List.of("p-1", "p-2", "p-3", "p-4", "p-5"));
        assertThat(calls).as("issuer calls after building the Flux").hasValue(0);

        StepVerifier.create(all.take(2))
                .expectNext("SETTLED:p-1", "SETTLED:p-2")
                .verifyComplete();
        assertThat(calls).as("issuer calls for take(2)").hasValue(2);
    }

    @Test
    @DisplayName("counted() counts every subscription and nothing else")
    void countsSubscriptions() {
        AtomicInteger subscriptions = new AtomicInteger();
        Mono<String> mono = Subscriptions.counted(Mono.just("fx-rate"), subscriptions);
        assertThat(subscriptions).as("after building").hasValue(0);

        assertThat(mono.block()).isEqualTo("fx-rate");
        assertThat(mono.block()).isEqualTo("fx-rate");
        StepVerifier.create(mono).expectNext("fx-rate").verifyComplete();
        assertThat(subscriptions).as("after three subscriptions").hasValue(3);
    }
}
