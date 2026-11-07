package workbench.reactive.l08

import reactor.core.publisher.Flux
import reactor.core.publisher.Mono

// assembled here, far away from where it is subscribed: the merchant has two fee rows, the code expects one
private fun feeRow(merchant: String): Mono<Int> = Flux.just(120, 80).single()

private fun show(title: String, chain: Mono<Int>) {
    try {
        chain.block()
    } catch (e: RuntimeException) {
        val mentionsFeeRow = e.stackTrace.any { it.methodName.startsWith("feeRow") }
        println(title)
        println("   $e")
        println("   top frame: ${e.stackTrace[0]}")
        println("   any frame in feeRow(), where single() was written? $mentionsFeeRow")
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
    show("1. no help", feeRow("m-1").map { fee -> fee + 1 })
    show("2. checkpoint(\"fee-row\")", feeRow("m-1").checkpoint("fee-row").map { fee -> fee + 1 })
    show("3. checkpoint(\"fee-row\", true)", feeRow("m-1").checkpoint("fee-row", true).map { fee -> fee + 1 })

    println("4. log(\"rows\") between a range and take(2)")
    Flux.range(1, 5).log("rows").take(2).blockLast()
}
