package workbench.reactive.l04

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

/** zip pairs by position. Mono.zip with an empty source completes empty, and cancels the others. */
fun main() {
    println("Flux.zip: " + Flux.zip(Flux.just(1, 2, 3), Flux.just("a", "b")).collectList().block())

    val fxRate: Mono<String> = Mono.delay(Duration.ofMillis(200)).thenReturn("1.08")
        .doOnCancel { println("  fx rate call cancelled") }
    val fee: Mono<String> = Mono.delay(Duration.ofMillis(100)).thenReturn("0.30")
    val limit: Mono<String> = Mono.empty()                                   // no limit configured

    Mono.zip(fxRate, fee, limit)
        .doOnSuccess { t -> println("Mono.zip result: $t") }                 // null means "completed empty"
        .block()

    try {
        Mono.zip(fxRate, fee, limit.switchIfEmpty(Mono.error(IllegalStateException("missing limit"))))
            .block()
    } catch (e: IllegalStateException) {
        println("with switchIfEmpty: ${e.message}")
    }
}
