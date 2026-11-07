package workbench.kotlin.l03.demo

var rateCalls = 0

class FxQuote {
    /** Default mode: SYNCHRONIZED. The first reader runs the initializer under a lock. */
    val eurUsd: Double by lazy {
        rateCalls++
        if (rateCalls == 1) throw IllegalStateException("rate service timed out")
        1.0842
    }
}

fun main() {
    for (mode in LazyThreadSafetyMode.entries) {
        println("$mode -> ${lazy(mode) { 0 }.javaClass.name}")
    }

    val quote = FxQuote()
    try {
        quote.eurUsd
    } catch (e: IllegalStateException) {
        println("first read failed: ${e.message}")
    }
    println("second read: ${quote.eurUsd} (initializer ran $rateCalls times)")
    println("third read:  ${quote.eurUsd} (initializer ran $rateCalls times)")
    println("field: ${FxQuote::class.java.declaredFields.joinToString { "${it.type.name} ${it.name}" }}")
}
