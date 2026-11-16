package workbench.reactive.l04

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

/** zip pairs by position. Mono.zip with an empty source completes empty, and cancels the others. */
fun main() {
    println("Flux.zip: " + Flux.zip(Flux.just(1, 2, 3), Flux.just("a", "b")).collectList().block())

    val price: Mono<String> = Mono.delay(Duration.ofMillis(200)).thenReturn("24.00")
        .doOnCancel { println("  price lookup cancelled") }
    val deliveryFee: Mono<String> = Mono.delay(Duration.ofMillis(100)).thenReturn("3.50")
    val discount: Mono<String> = Mono.empty()                                // this customer has no discount

    Mono.zip(price, deliveryFee, discount)
        .doOnSuccess { t -> println("Mono.zip result: $t") }                 // null means "completed empty"
        .block()

    Mono.zip(price, deliveryFee, discount.defaultIfEmpty("0.00"))
        .doOnSuccess { t -> println("with defaultIfEmpty: $t") }
        .block()

    try {
        Mono.zip(price, deliveryFee, discount.switchIfEmpty(Mono.error(IllegalStateException("missing discount"))))
            .block()
    } catch (e: IllegalStateException) {
        println("with switchIfEmpty: ${e.message}")
    }
}
