package workbench.reactive.l02;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

/** A Flux and a Mono, subscribed with the three callbacks, with log() printing every signal. */
public class FirstFluxDemo {
    public static void main(String[] args) {
        Flux<String> authorizations = Flux.just("auth-1", "auth-2", "auth-3");
        authorizations
                .log()                                              // prints each signal that passes this point
                .subscribe(
                        a -> System.out.println("got " + a),         // onNext
                        e -> System.out.println("failed: " + e),     // onError
                        () -> System.out.println("done"));           // onComplete

        Mono<String> declined = Mono.error(new IllegalStateException("card declined"));
        declined.subscribe(s -> System.out.println("got " + s));     // no error callback: watch what happens
        System.out.println("main carries on");
    }
}
