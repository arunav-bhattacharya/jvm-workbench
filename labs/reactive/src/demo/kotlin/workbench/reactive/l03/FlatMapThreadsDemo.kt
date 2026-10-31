package workbench.reactive.l03

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono
import java.time.Duration

/** flatMap does not create threads. Its first request upstream is its concurrency. */
fun main() {
    println("1. synchronous inners:")
    Flux.range(1, 3)
        .flatMap { i -> Mono.fromCallable { "score $i on ${Thread.currentThread().name}" } }
        .doOnNext { s -> println("  $s") }
        .blockLast()

    println("2. asynchronous inners (Mono.delay runs on Reactor's parallel scheduler):")
    Flux.range(1, 3)
        .flatMap { i ->
            Mono.delay(Duration.ofMillis(100L * (4 - i)))
                .map { "score $i on ${Thread.currentThread().name}" }
        }
        .doOnNext { s -> println("  $s") }
        .blockLast()

    println("3. what each operator asks the source for (inners take 10 ms each):")
    demand("flatMap(f)   ", source().flatMap { call(it) })
    demand("flatMap(f, 2)", source().flatMap({ call(it) }, 2))
    demand("concatMap(f) ", source().concatMap { call(it) })
}

private fun source(): Flux<Int> = Flux.range(1, 6).doOnRequest { n -> print("$n ") }

private fun call(i: Int): Mono<Int> = Mono.delay(Duration.ofMillis(10)).thenReturn(i)

private fun demand(name: String, flux: Flux<Int>) {
    print("  $name requests: ")
    flux.blockLast()
    println()
}
