package workbench.reactive.l06;

import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.math.BigDecimal;
import java.time.Duration;

/** block() on a Reactor parallel thread is refused. flatMap composes instead. */
public class BlockInParallelDemo {
    static Mono<BigDecimal> rate() {                      // a non-blocking FX lookup
        return Mono.delay(Duration.ofMillis(20)).thenReturn(new BigDecimal("0.92"));
    }

    public static void main(String[] args) {
        // a timer emits on a parallel thread, just like a WebClient response emits on a Netty thread
        Mono<BigDecimal> usd = Mono.delay(Duration.ofMillis(10)).thenReturn(new BigDecimal("100"));

        try {
            usd.map(amount -> amount.multiply(rate().block())).block();
        } catch (IllegalStateException e) {
            System.out.println("1. block() inside map:  " + e.getMessage());
        }

        System.out.println("2. flatMap instead:     " + usd.flatMap(amount -> rate().map(amount::multiply)).block());

        System.out.println("3. Mono.just(..).block() inside map: "
                + usd.map(amount -> amount.multiply(Mono.just(new BigDecimal("0.92")).block())).block()
                + " (a shortcut, not a permission)");

        System.out.println("4. block() after publishOn(boundedElastic): "
                + usd.publishOn(Schedulers.boundedElastic()).map(amount -> amount.multiply(rate().block())).block());
    }
}
