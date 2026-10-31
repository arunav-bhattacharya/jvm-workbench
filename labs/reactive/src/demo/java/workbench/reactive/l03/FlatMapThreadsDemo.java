package workbench.reactive.l03;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;

/** flatMap does not create threads. Its first request upstream is its concurrency. */
public class FlatMapThreadsDemo {
    public static void main(String[] args) {
        System.out.println("1. synchronous inners:");
        Flux.range(1, 3)
                .flatMap(i -> Mono.fromCallable(() -> "score " + i + " on " + Thread.currentThread().getName()))
                .doOnNext(s -> System.out.println("  " + s))
                .blockLast();

        System.out.println("2. asynchronous inners (Mono.delay runs on Reactor's parallel scheduler):");
        Flux.range(1, 3)
                .flatMap(i -> Mono.delay(Duration.ofMillis(100L * (4 - i)))
                        .map(t -> "score " + i + " on " + Thread.currentThread().getName()))
                .doOnNext(s -> System.out.println("  " + s))
                .blockLast();

        System.out.println("3. what each operator asks the source for (inners take 10 ms each):");
        demand("flatMap(f)   ", Flux.range(1, 6).doOnRequest(n -> System.out.print(n + " ")).flatMap(FlatMapThreadsDemo::call));
        demand("flatMap(f, 2)", Flux.range(1, 6).doOnRequest(n -> System.out.print(n + " ")).flatMap(FlatMapThreadsDemo::call, 2));
        demand("concatMap(f) ", Flux.range(1, 6).doOnRequest(n -> System.out.print(n + " ")).concatMap(FlatMapThreadsDemo::call));
    }

    static Mono<Integer> call(int i) {
        return Mono.delay(Duration.ofMillis(10)).thenReturn(i);
    }

    static void demand(String name, Flux<Integer> flux) {
        System.out.print("  " + name + " requests: ");
        flux.blockLast();
        System.out.println();
    }
}
