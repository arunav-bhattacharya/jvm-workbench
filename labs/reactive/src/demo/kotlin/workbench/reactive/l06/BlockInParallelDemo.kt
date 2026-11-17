package workbench.reactive.l06

import reactor.core.publisher.Mono
import reactor.core.scheduler.Schedulers
import java.math.BigDecimal
import java.time.Duration

private fun pricePerLoaf(): Mono<BigDecimal> =             // a non-blocking price-list lookup
    Mono.delay(Duration.ofMillis(20)).thenReturn(BigDecimal("2.50"))

private fun worth(loaves: Int, price: BigDecimal): BigDecimal = price.multiply(BigDecimal.valueOf(loaves.toLong()))

/** block() on a Reactor parallel thread is refused. flatMap composes instead. */
fun main() {
    // a timer emits on a parallel thread, just as a non-blocking client delivers its answer on a Reactor thread
    val loaves: Mono<Int> = Mono.delay(Duration.ofMillis(10)).thenReturn(100)

    try {
        loaves.map { n -> worth(n, pricePerLoaf().block()!!) }.block()
    } catch (e: IllegalStateException) {
        println("1. block() inside map:  ${e.message}")
    }

    println("2. flatMap instead:     " + loaves.flatMap { n -> pricePerLoaf().map { p -> worth(n, p) } }.block())

    println("3. Mono.just(..).block() inside map: " +
        loaves.map { n -> worth(n, Mono.just(BigDecimal("2.50")).block()!!) }.block() +
        " (a shortcut, not a permission)")

    println("4. block() after publishOn(boundedElastic): " +
        loaves.publishOn(Schedulers.boundedElastic()).map { n -> worth(n, pricePerLoaf().block()!!) }.block())
}
