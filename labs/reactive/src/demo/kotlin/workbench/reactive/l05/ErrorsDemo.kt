package workbench.reactive.l05

import reactor.core.publisher.Flux

/** An error ends the stream. The error operators replace what is left with something else. */
fun main() {
    val fees: Flux<Int> = Flux.just(1, 2, 0, 4).map { i -> 8 / i }           // 8 / 0 throws

    fees.subscribe({ v -> println("raw: $v") }, { e -> println("raw: error $e") })

    println("onErrorReturn: " + fees.onErrorReturn(-1).collectList().block())

    println("onErrorResume: " + fees
        .onErrorResume { Flux.just(100, 200) }                              // switch to a fallback stream
        .collectList().block())

    fees.onErrorMap(ArithmeticException::class.java) { e -> IllegalStateException("bad fee table", e) }
        .subscribe({ }, { e -> println("onErrorMap: $e caused by ${e.cause}") })
}
