package workbench.kotlin.l01.demo

/** inline: the compiler pastes this body, and the lambda's body, into every caller. */
inline fun <T> timed(label: String, block: () -> T): T {
    val start = System.nanoTime()
    try {
        return block()
    } finally {
        println("$label took ${(System.nanoTime() - start) / 1_000} us")
    }
}

/** The same function without inline: the caller builds a Function0 object and calls through it. */
fun <T> timedNotInline(label: String, block: () -> T): T {
    val start = System.nanoTime()
    try {
        return block()
    } finally {
        println("$label took ${(System.nanoTime() - start) / 1_000} us")
    }
}

fun feeInline(amountMinor: Long): Long = timed("inline") { amountMinor * 3 / 100 }

fun feeNotInline(amountMinor: Long): Long = timedNotInline("not inline") { amountMinor * 3 / 100 }

fun main() {
    println("fee = ${feeInline(12_000)}")
    println("fee = ${feeNotInline(12_000)}")
}
