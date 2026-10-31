package workbench.reactive.l02

import reactor.core.publisher.Flux
import java.util.concurrent.atomic.AtomicInteger

/** Building a pipeline runs none of it. Subscribing runs all of it. */
fun main() {
    val mapped = AtomicInteger()

    val fees: Flux<Int> = Flux.range(1, 3)
        .map { cents ->
            mapped.incrementAndGet()
            cents * 100
        }
    println("after assembly: map ran ${mapped.get()} times")

    fees.subscribe { f -> println("fee $f") }
    println("after subscribe: map ran ${mapped.get()} times")

    // A classic bug: the result of filter() is thrown away, so the filter is never part of the chain.
    val amounts: Flux<Int> = Flux.just(5, 50, 500)
    amounts.filter { a -> a > 10 }
    amounts.subscribe { a -> println("amount $a") }
}
