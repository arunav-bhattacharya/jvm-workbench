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

class CakeFlowsTest {

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
    @DisplayName("iceAll: ices all 12 cakes with exactly 4 at the icing machine at most")
    void iceAllUsesFourNozzles() {
        Tracker icing = new Tracker();
        List<String> expected = new ArrayList<>();
        for (int i = 1; i <= 12; i++) expected.add("c-" + i + ":iced");

        StepVerifier.withVirtualTime(() -> CakeFlows.iceAll(
                        Flux.range(1, 12).map(i -> "c-" + i),
                        id -> icing.call(id + ":iced", 50L * (1 + Integer.parseInt(id.substring(2)) % 3))))
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(10))
                .recordWith(ArrayList::new)
                .expectNextCount(12)
                .consumeRecordedWith(iced -> assertThat(iced).containsExactlyInAnyOrderElementsOf(expected))
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(icing.maxInFlight).as("max cakes at the icing machine").hasValue(4);
    }

    @Test
    @DisplayName("stackLayers: places strictly one layer at a time, and results keep stacking order")
    void stackLayersInOrder() {
        Tracker stacker = new Tracker();
        // the bottom layer is the slowest, so anything concurrent would finish out of order
        StepVerifier.withVirtualTime(() -> CakeFlows.stackLayers(
                        Flux.just("base-300", "cream-100", "sponge-200", "top-50"),
                        layer -> stacker.call("set:" + layer, Long.parseLong(layer.substring(layer.indexOf('-') + 1)))))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(299))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("set:base-300")
                .thenAwait(Duration.ofMillis(100))
                .expectNext("set:cream-100")
                .thenAwait(Duration.ofMillis(200))
                .expectNext("set:sponge-200")
                .thenAwait(Duration.ofMillis(50))
                .expectNext("set:top-50")
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(stacker.maxInFlight).as("max layers being placed at once").hasValue(1);
    }

    @Test
    @DisplayName("stackLayers: after a layer fails, later layers are never placed")
    void stackLayersStopsAtFailure() {
        Tracker stacker = new Tracker();
        StepVerifier.withVirtualTime(() -> CakeFlows.stackLayers(
                        Flux.just("layer-1", "layer-2", "layer-3"),
                        layer -> layer.equals("layer-2")
                                ? stacker.call("x", 10).then(Mono.error(new IllegalStateException("layer collapsed")))
                                : stacker.call("set:" + layer, 10)))
                .expectSubscription()
                .thenAwait(Duration.ofSeconds(1))
                .expectNext("set:layer-1")
                .expectErrorMessage("layer collapsed")
                .verify(Duration.ofSeconds(5));

        assertThat(stacker.started).as("layers placed").hasValue(2);
    }

    @Test
    @DisplayName("latestPrices: a newer pick cancels the price still on its way for the older one")
    void latestPriceWins() {
        Tracker prices = new Tracker();
        // picks at 0 ms (small), 50 ms (medium) and 300 ms (large); each price takes 100 ms
        StepVerifier.withVirtualTime(() -> CakeFlows.latestPrices(
                        Flux.concat(
                                Mono.just("small"),
                                Mono.just("medium").delayElement(Duration.ofMillis(50)),
                                Mono.just("large").delayElement(Duration.ofMillis(250))),
                        size -> prices.call(size + "=price", 100)))
                .expectSubscription()
                .expectNoEvent(Duration.ofMillis(149))
                .thenAwait(Duration.ofMillis(1))
                .expectNext("medium=price")                   // at 150 ms; small was abandoned at 50 ms
                .thenAwait(Duration.ofMillis(250))
                .expectNext("large=price")                    // at 400 ms
                .expectComplete()
                .verify(Duration.ofSeconds(5));

        assertThat(prices.cancelled).as("prices cancelled").hasValue(1);
    }
}
