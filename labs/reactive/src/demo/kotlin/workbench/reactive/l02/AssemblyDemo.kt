package workbench.reactive.l02

import reactor.core.publisher.Flux
import java.util.concurrent.atomic.AtomicInteger

/** Building a pipeline runs none of it. Subscribing runs all of it. */
fun main() {
    val mapped = AtomicInteger()

    val pricesInCents: Flux<Int> = Flux.range(1, 3)
        .map { euros ->
            mapped.incrementAndGet()
            euros * 100
        }
    println("after assembly: map ran ${mapped.get()} times")

    pricesInCents.subscribe { p -> println("price $p cents") }
    println("after subscribe: map ran ${mapped.get()} times")

    // A classic bug: the result of filter() is thrown away, so the filter is never part of the chain.
    val orderSizes: Flux<Int> = Flux.just(5, 50, 500)
    orderSizes.filter { loaves -> loaves > 10 }
    orderSizes.subscribe { loaves -> println("big order: $loaves loaves") }
}
