package workbench.patterns.l06

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger

class MerchantCategory private constructor(val code: String, val description: String) {
    init {
        created.incrementAndGet()
    }

    override fun toString() = "$code $description"

    companion object {
        private val created = AtomicInteger()
        private val pool = ConcurrentHashMap<String, MerchantCategory>()

        val instancesCreated: Int get() = created.get()

        val KNOWN: Map<String, String> = mapOf(
            "4111" to "Commuter transport",
            "5411" to "Grocery stores, supermarkets",
            "5812" to "Restaurants",
            "5999" to "Miscellaneous retail",
        )

        fun of(code: String): MerchantCategory {
            // 1. reject unknown codes first, so the pool can only hold the KNOWN set (it can't grow without bound)
            val description = requireNotNull(KNOWN[code]) { "unknown MCC: $code" }
            // 2. computeIfAbsent checks and inserts in one atomic step: the constructor runs at most once per code.
            //    `pool[code] ?: MerchantCategory(...).also { pool[code] = it }` would be check-then-act.
            return pool.computeIfAbsent(code) { MerchantCategory(it, description) }
        }
    }
}
