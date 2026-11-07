package workbench.patterns.l06

import java.util.Currency
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

// Four flyweights: three from the JDK, one of our own. In Kotlin, `==` is equals(); `===` asks "the same object?"

// our own: one shared instance per merchant category code
class MccCode private constructor(val code: String) {
    init { built.incrementAndGet() }

    companion object {
        private val pool = ConcurrentHashMap<String, MccCode>()
        private val built = AtomicInteger()
        fun of(code: String): MccCode = pool.computeIfAbsent(code) { MccCode(it) }
        val instancesBuilt: Int get() = built.get()
    }
}

fun main() {
    // typed as Any so Kotlin boxes them, as Java does for Integer; === on Int? gets a compiler warning
    val a: Any = 127
    val b: Any = 127
    val c: Any = 128
    val d: Any = 128
    println("Integer 127 === 127: ${a === b}")
    println("Integer 128 === 128: ${c === d}   ==: ${c == d}")

    val parsed = String(charArrayOf('5', '4', '1', '1'))   // a fresh object, like a field parsed from a message
    println("parsed === \"5411\": ${parsed === "5411"}   after intern(): ${parsed.intern() === "5411"}")

    println("Currency EUR === EUR: ${Currency.getInstance("EUR") === Currency.getInstance("EUR")}")

    val first = MccCode.of("5411")
    val second = MccCode.of("5411")
    println("Mcc 5411 === 5411: ${first === second}   instances built: ${MccCode.instancesBuilt}")
}
