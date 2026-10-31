package workbench.reactive.l04;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.math.BigDecimal;
import java.time.Duration;

/** A EUR limit and a EUR/USD rate that change at different times. zip vs combineLatest. */
public class CombineLatestDemo {
    static Flux<BigDecimal> limits() {     // 1000 at 0 ms, 2000 at 300 ms
        return Flux.concat(Mono.just(new BigDecimal("1000")), Mono.just(new BigDecimal("2000")).delayElement(Duration.ofMillis(300)));
    }

    static Flux<BigDecimal> rates() {      // 1.10 at 100 ms, 1.20 at 200 ms, 1.15 at 400 ms
        return Flux.just("1.10", "1.20", "1.15").map(BigDecimal::new)
                .zipWith(Flux.just(100L, 100L, 200L), (rate, wait) -> Mono.just(rate).delayElement(Duration.ofMillis(wait)))
                .concatMap(m -> m);
    }

    public static void main(String[] args) {
        System.out.println("zip:           " + Flux.zip(limits(), rates(), BigDecimal::multiply).collectList().block());
        System.out.println("combineLatest: " + Flux.combineLatest(limits(), rates(), BigDecimal::multiply).collectList().block());
    }
}
