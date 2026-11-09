package workbench.functional.l03.demo

var lastNanos = 0L

// Not inline: the lambda becomes an object, and a var it changes becomes a Ref box.
fun <T> measured(block: () -> T): T {
    val start = System.nanoTime()
    val result = block()
    lastNanos = System.nanoTime() - start
    return result
}

// Inline: the compiler pastes this body, and the lambda's body, into every caller.
inline fun <T> measuredInline(block: () -> T): T {
    val start = System.nanoTime()
    val result = block()
    lastNanos = System.nanoTime() - start
    return result
}

fun totalWithLambda(amounts: List<Long>): Long {
    var total = 0L
    measured { for (a in amounts) total += a }
    return total
}

fun totalInlined(amounts: List<Long>): Long {
    var total = 0L
    measuredInline { amounts.forEach { total += it } }
    return total
}

fun main() {
    val amounts = listOf(1_500L, 9_900L, 2_000L)
    println("with a lambda object: ${totalWithLambda(amounts)}")
    println("inlined:              ${totalInlined(amounts)}")
}
