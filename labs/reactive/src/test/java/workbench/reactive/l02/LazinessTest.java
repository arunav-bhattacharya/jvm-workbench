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

    private final OrderBook book = orderId -> {
        calls.incrementAndGet();
        if (orderId.equals("boom")) throw new IllegalStateException("order book down");
        if (orderId.equals("unknown")) return null;
        return "READY:" + orderId;
    };

    @Test
    @DisplayName("status() makes no order book call until someone subscribes")
    void noCallAtAssembly() {
        new OrderLookup(book).status("o-1");
        assertThat(calls).as("order book calls after building the Mono").hasValue(0);
    }

    @Test
    @DisplayName("status() calls the order book once per subscription")
    void oneCallPerSubscription() {
        Mono<String> status = new OrderLookup(book).status("o-1");
        assertThat(status.block()).isEqualTo("READY:o-1");
        assertThat(status.block()).isEqualTo("READY:o-1");
        assertThat(calls).as("order book calls after two subscriptions").hasValue(2);
    }

    @Test
    @DisplayName("an order book failure arrives as onError, not as an exception from status()")
    void failureIsASignal() {
        Mono<String> status = new OrderLookup(book).status("boom");   // must not throw here
        StepVerifier.create(status)
                .expectErrorMessage("order book down")
                .verify();
    }

    @Test
    @DisplayName("an unknown order (the order book returns null) gives an empty Mono")
    void nullIsEmpty() {
        StepVerifier.create(new OrderLookup(book).status("unknown"))
                .verifyComplete();
    }

    @Test
    @DisplayName("statuses() only calls the order book for items the subscriber requests")
    void statusesAreLazy() {
        var lookup = new OrderLookup(book);
        var all = lookup.statuses(List.of("o-1", "o-2", "o-3", "o-4", "o-5"));
        assertThat(calls).as("order book calls after building the Flux").hasValue(0);

        StepVerifier.create(all.take(2))
                .expectNext("READY:o-1", "READY:o-2")
                .verifyComplete();
        assertThat(calls).as("order book calls for take(2)").hasValue(2);
    }

    @Test
    @DisplayName("counted() counts every subscription and nothing else")
    void countsSubscriptions() {
        AtomicInteger subscriptions = new AtomicInteger();
        Mono<String> mono = Subscriptions.counted(Mono.just("price list"), subscriptions);
        assertThat(subscriptions).as("after building").hasValue(0);

        assertThat(mono.block()).isEqualTo("price list");
        assertThat(mono.block()).isEqualTo("price list");
        StepVerifier.create(mono).expectNext("price list").verifyComplete();
        assertThat(subscriptions).as("after three subscriptions").hasValue(3);
    }
}
