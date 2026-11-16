package workbench.reactive.l02;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/** A Flux and a Mono, subscribed with the three callbacks, with log() printing every signal. */
public class FirstFluxDemo {
    public static void main(String[] args) {
        Flux<String> loaves = Flux.just("rye-1", "rye-2", "rye-3");
        loaves
                .log()                                              // prints each signal that passes this point
                .subscribe(
                        l -> System.out.println("got " + l),         // onNext
                        e -> System.out.println("failed: " + e),     // onError
                        () -> System.out.println("done"));           // onComplete

        Mono<String> cake = Mono.error(new IllegalStateException("out of flour"));
        cake.subscribe(c -> System.out.println("got " + c));         // no error callback: watch what happens
        System.out.println("main carries on");
    }
}
