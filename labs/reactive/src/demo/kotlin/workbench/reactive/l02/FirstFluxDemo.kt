package workbench.reactive.l02

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

/** A Flux and a Mono, subscribed with the three callbacks, with log() printing every signal. */
fun main() {
    val loaves: Flux<String> = Flux.just("rye-1", "rye-2", "rye-3")
    loaves
        .log()                                              // prints each signal that passes this point
        .subscribe(
            { l -> println("got $l") },                     // onNext
            { e -> println("failed: $e") },                 // onError
            { println("done") })                            // onComplete

    val cake: Mono<String> = Mono.error(IllegalStateException("out of flour"))
    cake.subscribe { c -> println("got $c") }               // no error callback: watch what happens
    println("main carries on")
}
