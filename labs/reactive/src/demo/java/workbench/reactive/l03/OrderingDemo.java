package workbench.reactive.l03;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.function.Function;

/** Source 3, 1, 2. Item i takes i x 100 ms. Same input, three operators. */
public class OrderingDemo {
    static Mono<Integer> slowCall(int i) {
        return Mono.delay(Duration.ofMillis(i * 100L)).thenReturn(i);
    }

    public static void main(String[] args) {
        Flux.just(1).flatMap(i -> Mono.delay(Duration.ofMillis(1))).blockLast();   // warm up, so timings are fair
        run("flatMap          ", src -> src.flatMap(OrderingDemo::slowCall));
        run("concatMap        ", src -> src.concatMap(OrderingDemo::slowCall));
        run("flatMapSequential", src -> src.flatMapSequential(OrderingDemo::slowCall));
    }

    static void run(String name, Function<Flux<Integer>, Flux<Integer>> operator) {
        long t0 = System.nanoTime();
        var out = operator.apply(Flux.just(3, 1, 2)).collectList().block();
        long ms = (System.nanoTime() - t0) / 1_000_000;
        System.out.printf("%s -> %s in about %d ms%n", name, out, Math.round(ms / 100.0) * 100);
    }
}
