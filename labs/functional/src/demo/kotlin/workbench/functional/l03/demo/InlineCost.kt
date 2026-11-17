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

fun totalWithLambda(grams: List<Long>): Long {
    var total = 0L
    measured { for (g in grams) total += g }
    return total
}

fun totalInlined(grams: List<Long>): Long {
    var total = 0L
    measuredInline { grams.forEach { total += it } }
    return total
}

fun main() {
    val grams = listOf(500L, 250L, 1_000L)             // flour, sugar and milk for one cake
    println("with a lambda object: ${totalWithLambda(grams)}")
    println("inlined:              ${totalInlined(grams)}")
}
