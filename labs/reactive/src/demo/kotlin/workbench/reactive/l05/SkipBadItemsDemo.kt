package workbench.reactive.l05

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

/** Skipping bad items: handle the error inside each item's own Mono, not on the whole stream. */
fun main() {
    val amounts: Flux<Int> = Flux.just(1, 2, 0, 4)

    val whole = amounts.map { i -> 8 / i }.onErrorResume { Mono.empty() }.collectList().block()
    println("onErrorResume on the stream: $whole")

    val perItem = amounts
        .concatMap { i ->
            Mono.fromCallable { 8 / i }
                .doOnError { e -> println("  skipping $i: ${e.message}") }
                .onErrorResume { Mono.empty() }                            // only this item's Mono ends
        }
        .collectList().block()
    println("onErrorResume per item:      $perItem")

    val continued = amounts.map { i -> 8 / i }
        .onErrorContinue { _, item -> println("  onErrorContinue dropped $item") }
        .collectList().block()
    println("onErrorContinue:             $continued")
}
