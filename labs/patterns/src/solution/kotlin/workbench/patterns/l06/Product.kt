package workbench.patterns.l06

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

class Product private constructor(val code: String, val name: String) {
    init {
        created.incrementAndGet()
    }

    override fun toString() = "$code $name"

    companion object {
        private val created = AtomicInteger()
        private val pool = ConcurrentHashMap<String, Product>()

        val instancesCreated: Int get() = created.get()

        val CATALOG: Map<String, String> = mapOf(
            "T-1001" to "Breakfast tea",
            "J-2001" to "Strawberry jam",
            "B-3001" to "Rye bread",
            "C-4001" to "Coffee beans",
        )

        fun of(code: String): Product {
            // 1. reject unknown codes first, so the pool can only hold the catalog (it can't grow without bound)
            val name = requireNotNull(CATALOG[code]) { "unknown product: $code" }
            // 2. computeIfAbsent checks and inserts in one atomic step: the constructor runs at most once per code.
            //    `pool[code] ?: Product(...).also { pool[code] = it }` would be check-then-act.
            return pool.computeIfAbsent(code) { Product(it, name) }
        }
    }
}
