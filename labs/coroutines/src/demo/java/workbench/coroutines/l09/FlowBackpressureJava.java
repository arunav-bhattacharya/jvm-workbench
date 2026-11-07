// Java equivalent of FlowBackpressure.kt with Reactor: concatMap with prefetch 0 (ask for the
// next tick only when the last one is priced) is close to a plain flow, onBackpressureBuffer to buffer(), onBackpressureLatest to conflate(), and switchMap
// to collectLatest (a new tick cancels the work on the previous one).
package workbench.coroutines.l09;

import java.time.Duration;
import java.util.function.Function;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

public class FlowBackpressureJava {
    /** Three FX ticks, 100 ms apart, produced only when asked for (like a cold flow). */
    static Flux<Integer> ticks() {
        return Flux.range(1, 3).concatMap(i -> Mono.just(i).delayElement(Duration.ofMillis(100)), 1);
    }

    /** Pricing a quote book: 300 ms per tick. */
    static Mono<Integer> price(int i) {
        return Mono.just(i).delayElement(Duration.ofMillis(300)).doOnNext(x -> System.out.print(x + " "));
    }

    static void time(String label, Function<Flux<Integer>, Flux<Integer>> pipeline) {
        long t0 = System.nanoTime();
        pipeline.apply(ticks()).blockLast();
        System.out.printf(" %-26s %d ms%n", label, (System.nanoTime() - t0) / 1_000_000);
    }

    public static void main(String[] args) {
        time("concatMap, prefetch 0:", f -> f.concatMap(FlowBackpressureJava::price, 0));
        time("onBackpressureBuffer:", f -> f.onBackpressureBuffer().concatMap(FlowBackpressureJava::price, 0));
        time("onBackpressureLatest:", f -> f.onBackpressureLatest().concatMap(FlowBackpressureJava::price, 0));
        time("switchMap:", f -> f.switchMap(FlowBackpressureJava::price));
    }
}
