package workbench.coroutines.l10

import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

fun interface UnitConverter {
    suspend fun toGrams(amount: Long, unit: String): Long
}

class ShoppingList(private val units: UnitConverter) {
    private val grams = HashMap<String, Long>() // only touched while holding the mutex
    private val mutex = Mutex()

    suspend fun add(item: String, amount: Long, unit: String) {
        // 1. the slow, suspending part runs outside the lock, so conversions overlap
        val more = units.toGrams(amount, unit)
        // 2. the read-modify-write is one critical section with no suspension inside.
        //    Mutex.withLock suspends (it doesn't block a thread) while another helper holds it.
        mutex.withLock {
            grams[item] = (grams[item] ?: 0L) + more
        }
    }

    suspend fun total(item: String): Long = mutex.withLock { grams[item] ?: 0L }
}
