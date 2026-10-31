package workbench.reactive.l04

import reactor.core.publisher.Flux
import java.time.Duration
import kotlin.math.roundToLong

private var t0 = 0L
private fun ms() = (System.nanoTime() - t0) / 1_000_000

private fun card(): Flux<String> =
    Flux.interval(Duration.ofMillis(30)).map { i -> "card-$i" }.take(3)
        .doOnSubscribe { println("  [%3d ms] card subscribed".format(ms())) }

private fun bank(): Flux<String> =
    Flux.interval(Duration.ofMillis(40)).map { i -> "bank-$i" }.take(3)
        .doOnSubscribe { println("  [%3d ms] bank subscribed".format(ms())) }

/** Two event sources: card events every 30 ms, bank events every 40 ms. Three ways to combine them. */
fun main() {
    // warm up, so the first timing doesn't include class loading
    Flux.merge(Flux.interval(Duration.ofMillis(1)).take(2), Flux.just(9L)).concatWith(Flux.mergeSequential(Flux.just(1L))).blockLast()
    "%3d".format(0)
    run("merge") { a, b -> Flux.merge(a, b) }
    run("concat") { a, b -> Flux.concat(a, b) }
    run("mergeSequential") { a, b -> Flux.mergeSequential(a, b) }
}

private fun run(name: String, combine: (Flux<String>, Flux<String>) -> Flux<String>) {
    println("$name:")
    t0 = System.nanoTime()
    val out = combine(card(), bank()).collectList().block()
    println("  $out, done at about ${(ms() / 10.0).roundToLong() * 10} ms")
}
