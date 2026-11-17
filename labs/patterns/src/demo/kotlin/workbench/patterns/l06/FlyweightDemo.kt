package workbench.patterns.l06

import java.util.Currency
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

// Four flyweights: three from the JDK, one of our own. In Kotlin, `==` is equals(); `===` asks "the same object?"

// our own: one shared instance per product code in the shop's catalog
class CatalogProduct private constructor(val code: String) {
    init { built.incrementAndGet() }

    companion object {
        private val pool = ConcurrentHashMap<String, CatalogProduct>()
        private val built = AtomicInteger()
        fun of(code: String): CatalogProduct = pool.computeIfAbsent(code) { CatalogProduct(it) }
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

    val parsed = String("T-1001".toCharArray())            // a fresh object, like a code read from an order form
    println("parsed === \"T-1001\": ${parsed === "T-1001"}   after intern(): ${parsed.intern() === "T-1001"}")

    println("Currency EUR === EUR: ${Currency.getInstance("EUR") === Currency.getInstance("EUR")}")

    val first = CatalogProduct.of("T-1001")
    val second = CatalogProduct.of("T-1001")
    println("Product T-1001 === T-1001: ${first === second}   instances built: ${CatalogProduct.instancesBuilt}")
}
