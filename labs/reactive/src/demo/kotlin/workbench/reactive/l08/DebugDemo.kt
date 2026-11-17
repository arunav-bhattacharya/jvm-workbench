package workbench.reactive.l08

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

// assembled here, far away from where it is subscribed: the cake has two price rows, the code expects one
private fun priceRow(cake: String): Mono<Int> = Flux.just(2400, 2600).single()

private fun show(title: String, chain: Mono<Int>) {
    try {
        chain.block()
    } catch (e: RuntimeException) {
        val mentionsPriceRow = e.stackTrace.any { it.methodName.startsWith("priceRow") }
        println(title)
        println("   $e")
        println("   top frame: ${e.stackTrace[0]}")
        println("   any frame in priceRow(), where single() was written? $mentionsPriceRow")
        for (s in e.suppressed) {
            s.message.orEmpty().lines()
                .filter { it.isNotBlank() && "#block" !in it }
                .take(4)
                .map { it.replace("⇢", "->") }                      // Reactor prints an arrow here
                .forEach { println("   ${it.trim()}") }
        }
    }
}

/** Where did it fail? An operator error without help, with checkpoints, and the signals log() shows. */
fun main() {
    show("1. no help", priceRow("chocolate").map { cents -> cents + 100 })
    show("2. checkpoint(\"price-row\")", priceRow("chocolate").checkpoint("price-row").map { cents -> cents + 100 })
    show("3. checkpoint(\"price-row\", true)", priceRow("chocolate").checkpoint("price-row", true).map { cents -> cents + 100 })

    println("4. log(\"rows\") between a range and take(2)")
    Flux.range(1, 5).log("rows").take(2).blockLast()
}
