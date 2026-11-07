package workbench.reactive.l06

import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.math.BigDecimal
import java.time.Duration

private fun rate(): Mono<BigDecimal> =                     // a non-blocking FX lookup
    Mono.delay(Duration.ofMillis(20)).thenReturn(BigDecimal("0.92"))

/** block() on a Reactor parallel thread is refused. flatMap composes instead. */
fun main() {
    // a timer emits on a parallel thread, just like a WebClient response emits on a Netty thread
    val usd: Mono<BigDecimal> = Mono.delay(Duration.ofMillis(10)).thenReturn(BigDecimal("100"))

    try {
        usd.map { amount -> amount.multiply(rate().block()) }.block()
    } catch (e: IllegalStateException) {
        println("1. block() inside map:  ${e.message}")
    }

    println("2. flatMap instead:     " + usd.flatMap { amount -> rate().map(amount::multiply) }.block())

    println("3. Mono.just(..).block() inside map: " +
        usd.map { amount -> amount.multiply(Mono.just(BigDecimal("0.92")).block()) }.block() +
        " (a shortcut, not a permission)")

    println("4. block() after publishOn(boundedElastic): " +
        usd.publishOn(Schedulers.boundedElastic()).map { amount -> amount.multiply(rate().block()) }.block())
}
