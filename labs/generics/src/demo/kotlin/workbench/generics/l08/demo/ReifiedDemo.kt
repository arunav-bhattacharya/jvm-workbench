package workbench.generics.l08.demo

/** inline copies the body into each caller; reified copies the caller's real T in with it. */
inline fun <reified T> Any?.isA(): Boolean = this is T

inline fun <reified T : Any> nameOf(): String = T::class.java.simpleName

fun main() {
    val payload: List<Any?> = listOf("pay_1", 1_200L, null, "pay_2", 2.5)

    println("\"pay_1\".isA<String>() = ${"pay_1".isA<String>()}, 1200L.isA<String>() = ${1_200L.isA<String>()}")
    println("strings: ${payload.filterIsInstance<String>()}")   // the stdlib's reified filter
    println("longs:   ${payload.filterIsInstance<Long>()}")
    println("nameOf<java.math.BigDecimal>() = ${nameOf<java.math.BigDecimal>()}")
}

// Wrong moves. Uncomment one at a time, predict the error, then run.
// fun <reified T> notInline(x: Any) = x is T          // 1
// fun <T> forward(x: Any) = x.isA<T>()               // 2
