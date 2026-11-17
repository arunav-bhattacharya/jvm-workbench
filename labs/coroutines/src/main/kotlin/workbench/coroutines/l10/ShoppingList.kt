package workbench.coroutines.l10

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Converts an amount to grams. It looks the unit up in the recipe app, so it suspends. */
fun interface UnitConverter {
    suspend fun toGrams(amount: Long, unit: String): Long
}

/**
 * One shopping list for the whole dinner: grams needed per item, written on by many helpers at once.
 *
 * Rules:
 * - Every addition must land: 100 helpers each adding one 100 g scoop of flour add exactly 10,000 g.
 * - Conversions (the slow, suspending part) may run at the same time; only the update of the
 *   list itself must be one at a time.
 *
 * Bug: limitedParallelism(1) runs one coroutine at a time, but only BETWEEN suspension points.
 * Each addition reads the list, suspends in toGrams, and writes later, so additions overwrite
 * each other.
 */
class ShoppingList(private val units: UnitConverter) {
    private val grams = HashMap<String, Long>()
    private val oneAtATime = Dispatchers.Default.limitedParallelism(1, "shopping-list")

    suspend fun add(item: String, amount: Long, unit: String) {
        withContext(oneAtATime) {
            val before = grams[item] ?: 0L
            val more = units.toGrams(amount, unit) // suspends: another helper writes here
            grams[item] = before + more
        }
    }

    suspend fun total(item: String): Long = withContext(oneAtATime) { grams[item] ?: 0L }
}
