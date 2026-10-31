package workbench.reactive.l04

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.math.BigDecimal
import java.time.Duration

// 1000 at 0 ms, 2000 at 300 ms
private fun limits(): Flux<BigDecimal> =
    Flux.concat(Mono.just(BigDecimal("1000")), Mono.just(BigDecimal("2000")).delayElement(Duration.ofMillis(300)))

// 1.10 at 100 ms, 1.20 at 200 ms, 1.15 at 400 ms
private fun rates(): Flux<BigDecimal> =
    Flux.just("1.10", "1.20", "1.15").map { BigDecimal(it) }
        .zipWith(Flux.just(100L, 100L, 200L)) { rate, wait -> Mono.just(rate).delayElement(Duration.ofMillis(wait)) }
        .concatMap { it }

/** A EUR limit and a EUR/USD rate that change at different times. zip vs combineLatest. */
fun main() {
    println("zip:           " + Flux.zip(limits(), rates()) { l, r -> l.multiply(r) }.collectList().block())
    println("combineLatest: " + Flux.combineLatest(limits(), rates()) { l, r -> l.multiply(r) }.collectList().block())
}
