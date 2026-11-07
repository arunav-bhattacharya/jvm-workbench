@file:OptIn(ExperimentalStdlibApi::class)

package workbench.kotlin.l02.demo

/**
 * @JvmExposeBoxed (Experimental since Kotlin 2.2.0) adds Java-friendly members next to the
 * mangled ones: a public constructor that runs init, and overloads that take and return the box.
 */
@JvmExposeBoxed
@JvmInline
value class Fee(val minor: Long) {
    init {
        require(minor >= 0) { "negative fee: $minor" }
    }

    fun doubled(): Fee = Fee(minor * 2)
}

@JvmExposeBoxed
fun describeFee(fee: Fee): String = "fee of ${fee.minor} minor units"

fun main() {
    println(describeFee(Fee(125).doubled()))
}
