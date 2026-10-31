package workbench.reactive.l03

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration
import kotlin.math.roundToLong

private fun slowCall(i: Int): Mono<Int> = Mono.delay(Duration.ofMillis(i * 100L)).thenReturn(i)

/** Source 3, 1, 2. Item i takes i x 100 ms. Same input, three operators. */
fun main() {
    Flux.just(1).flatMap { Mono.delay(Duration.ofMillis(1)) }.blockLast()   // warm up, so timings are fair
    run("flatMap          ") { src -> src.flatMap { slowCall(it) } }
    run("concatMap        ") { src -> src.concatMap { slowCall(it) } }
    run("flatMapSequential") { src -> src.flatMapSequential { slowCall(it) } }
}

private fun run(name: String, operator: (Flux<Int>) -> Flux<Int>) {
    val t0 = System.nanoTime()
    val out = operator(Flux.just(3, 1, 2)).collectList().block()
    val ms = (System.nanoTime() - t0) / 1_000_000
    println("$name -> $out in about ${(ms / 100.0).roundToLong() * 100} ms")
}
