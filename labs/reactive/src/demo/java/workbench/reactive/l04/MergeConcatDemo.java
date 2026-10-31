package workbench.reactive.l04;

import reactor.core.publisher.Flux;

import java.time.Duration;
import java.util.function.BiFunction;

/** Two event sources: card events every 30 ms, bank events every 40 ms. Three ways to combine them. */
public class MergeConcatDemo {
    static Flux<String> card() {
        return Flux.interval(Duration.ofMillis(30)).map(i -> "card-" + i).take(3)
                .doOnSubscribe(s -> System.out.printf("  [%3d ms] card subscribed%n", ms()));
    }

    static Flux<String> bank() {
        return Flux.interval(Duration.ofMillis(40)).map(i -> "bank-" + i).take(3)
                .doOnSubscribe(s -> System.out.printf("  [%3d ms] bank subscribed%n", ms()));
    }

    static long t0;

    static long ms() {
        return (System.nanoTime() - t0) / 1_000_000;
    }

    public static void main(String[] args) {
        // warm up, so the first timing doesn't include class loading
        Flux.merge(Flux.interval(Duration.ofMillis(1)).take(2), Flux.just(9L)).concatWith(Flux.mergeSequential(Flux.just(1L))).blockLast();
        String.format("%3d", 0);
        run("merge", Flux::merge);
        run("concat", Flux::concat);
        run("mergeSequential", Flux::mergeSequential);
    }

    static void run(String name, BiFunction<Flux<String>, Flux<String>, Flux<String>> combine) {
        System.out.println(name + ":");
        t0 = System.nanoTime();
        var out = combine.apply(card(), bank()).collectList().block();
        System.out.printf("  %s, done at about %d ms%n", out, Math.round(ms() / 10.0) * 10);
    }
}
