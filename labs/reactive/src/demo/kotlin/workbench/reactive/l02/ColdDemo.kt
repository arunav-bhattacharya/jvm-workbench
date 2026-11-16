package workbench.reactive.l02

import reactor.core.publisher.Mono
import java.util.concurrent.atomic.AtomicInteger

private val baked = AtomicInteger()

/** A cold Mono does its work again for every subscriber. Here the work is baking a cake. */
private fun bake(orderId: String): Mono<String> =
    Mono.fromCallable {
        val n = baked.incrementAndGet()
        println("  oven: baking the cake for $orderId (cake #$n)")
        "cake-$n"
    }

fun main() {
    val cake = bake("order-42")

    cake.subscribe { c -> println("shop log: $c") }      // subscriber 1
    val handedOver = cake.block()                        // subscriber 2
    println("handed to the customer: $handedOver")
    println("cakes baked: ${baked.get()}")
}
