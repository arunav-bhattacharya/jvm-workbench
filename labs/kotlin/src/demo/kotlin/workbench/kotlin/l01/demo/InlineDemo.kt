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

/** The shop's rule of thumb: 3 ml of ink for every 100 pages. */
fun inkInline(pages: Long): Long = timed("inline") { pages * 3 / 100 }

fun inkNotInline(pages: Long): Long = timedNotInline("not inline") { pages * 3 / 100 }

fun main() {
    println("ink = ${inkInline(12_000)} ml")
    println("ink = ${inkNotInline(12_000)} ml")
}
