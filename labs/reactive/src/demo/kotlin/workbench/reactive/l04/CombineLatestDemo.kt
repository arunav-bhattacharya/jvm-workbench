package workbench.reactive.l04

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.math.BigDecimal
import java.time.Duration

// 1.5 kg at 0 ms, 2.0 kg at 300 ms
private fun weights(): Flux<BigDecimal> =
    Flux.concat(Mono.just(BigDecimal("1.5")), Mono.just(BigDecimal("2.0")).delayElement(Duration.ofMillis(300)))

// 20.00 at 100 ms, 22.00 at 200 ms, 21.00 at 400 ms
private fun pricesPerKg(): Flux<BigDecimal> =
    Flux.just("20.00", "22.00", "21.00").map { BigDecimal(it) }
        .zipWith(Flux.just(100L, 100L, 200L)) { price, wait -> Mono.just(price).delayElement(Duration.ofMillis(wait)) }
        .concatMap { it }

/** A cake's weight and the price per kilogram change at different times. zip vs combineLatest. */
fun main() {
    println("zip:           " + Flux.zip(weights(), pricesPerKg()) { w, p -> w.multiply(p) }.collectList().block())
    println("combineLatest: " + Flux.combineLatest(weights(), pricesPerKg()) { w, p -> w.multiply(p) }.collectList().block())
}
