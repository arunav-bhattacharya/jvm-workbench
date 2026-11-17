package workbench.reactive.l05

import reactor.core.publisher.Flux

/** An error ends the stream. The error operators replace what is left with something else. */
fun main() {
    val perBox: Flux<Int> = Flux.just(1, 2, 0, 4).map { i -> 8 / i }         // 8 loaves into i boxes; 0 throws

    perBox.subscribe({ v -> println("raw: $v") }, { e -> println("raw: error $e") })

    println("onErrorReturn: " + perBox.onErrorReturn(-1).collectList().block())

    println("onErrorResume: " + perBox
        .onErrorResume { Flux.just(100, 200) }                              // switch to a backup stream
        .collectList().block())

    perBox.onErrorMap(ArithmeticException::class.java) { e -> IllegalStateException("bad box count", e) }
        .subscribe({ }, { e -> println("onErrorMap: $e caused by ${e.cause}") })
}
