package workbench.reactive.l02

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

/** A Flux and a Mono, subscribed with the three callbacks, with log() printing every signal. */
fun main() {
    val authorizations: Flux<String> = Flux.just("auth-1", "auth-2", "auth-3")
    authorizations
        .log()                                              // prints each signal that passes this point
        .subscribe(
            { a -> println("got $a") },                     // onNext
            { e -> println("failed: $e") },                 // onError
            { println("done") })                            // onComplete

    val declined: Mono<String> = Mono.error(IllegalStateException("card declined"))
    declined.subscribe { s -> println("got $s") }           // no error callback: watch what happens
    println("main carries on")
}
