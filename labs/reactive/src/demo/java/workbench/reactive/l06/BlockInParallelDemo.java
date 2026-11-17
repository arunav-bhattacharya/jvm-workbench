package workbench.reactive.l06;

import reactor.core.publisher.Mono;
import reactor.core.scheduler.Schedulers;

import java.math.BigDecimal;
import java.time.Duration;

/** block() on a Reactor parallel thread is refused. flatMap composes instead. */
public class BlockInParallelDemo {
    static Mono<BigDecimal> pricePerLoaf() {               // a non-blocking price-list lookup
        return Mono.delay(Duration.ofMillis(20)).thenReturn(new BigDecimal("2.50"));
    }

    static BigDecimal worth(int loaves, BigDecimal price) {
        return price.multiply(BigDecimal.valueOf(loaves));
    }

    public static void main(String[] args) {
        // a timer emits on a parallel thread, just as a non-blocking client delivers its answer on a Reactor thread
        Mono<Integer> loaves = Mono.delay(Duration.ofMillis(10)).thenReturn(100);

        try {
            loaves.map(n -> worth(n, pricePerLoaf().block())).block();
        } catch (IllegalStateException e) {
            System.out.println("1. block() inside map:  " + e.getMessage());
        }

        System.out.println("2. flatMap instead:     " + loaves.flatMap(n -> pricePerLoaf().map(p -> worth(n, p))).block());

        System.out.println("3. Mono.just(..).block() inside map: "
                + loaves.map(n -> worth(n, Mono.just(new BigDecimal("2.50")).block())).block()
                + " (a shortcut, not a permission)");

        System.out.println("4. block() after publishOn(boundedElastic): "
                + loaves.publishOn(Schedulers.boundedElastic()).map(n -> worth(n, pricePerLoaf().block())).block());
    }
}
