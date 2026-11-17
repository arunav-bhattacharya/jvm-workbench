@file:OptIn(ExperimentalStdlibApi::class)

package workbench.kotlin.l02.demo

/**
 * @JvmExposeBoxed (Experimental since Kotlin 2.2.0) adds Java-friendly members next to the
 * mangled ones: a public constructor that runs init, and overloads that take and return the box.
 */
@JvmExposeBoxed
@JvmInline
value class Copies(val count: Long) {
    init {
        require(count >= 0) { "negative copies: $count" }
    }

    fun doubled(): Copies = Copies(count * 2)
}

@JvmExposeBoxed
fun describeRun(copies: Copies): String = "a run of ${copies.count} copies"

fun main() {
    println(describeRun(Copies(125).doubled()))
}
