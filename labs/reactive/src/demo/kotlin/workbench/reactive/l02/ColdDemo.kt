package workbench.reactive.l02

import reactor.core.publisher.Mono
import java.util.concurrent.atomic.AtomicInteger

private val charges = AtomicInteger()

/** A cold Mono does its work again for every subscriber. Here the work is a card charge. */
private fun charge(paymentId: String): Mono<String> =
    Mono.fromCallable {
        val n = charges.incrementAndGet()
        println("  issuer: charging $paymentId (charge #$n)")
        "receipt-$n"
    }

fun main() {
    val charge = charge("pay-42")

    charge.subscribe { r -> println("audit log: $r") }   // subscriber 1
    val receipt = charge.block()                         // subscriber 2
    println("returned to caller: $receipt")
    println("charges made: ${charges.get()}")
}
