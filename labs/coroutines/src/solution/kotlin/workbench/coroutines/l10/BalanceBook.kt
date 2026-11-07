package workbench.coroutines.l10

import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

fun interface FxConverter {
    suspend fun toEurCents(amount: Long, currency: String): Long
}

class BalanceBook(private val fx: FxConverter) {
    private val balances = HashMap<String, Long>() // only touched while holding the mutex
    private val mutex = Mutex()

    suspend fun credit(account: String, amount: Long, currency: String) {
        // 1. the slow, suspending part runs outside the lock, so conversions overlap
        val cents = fx.toEurCents(amount, currency)
        // 2. the read-modify-write is one critical section with no suspension inside.
        //    Mutex.withLock suspends (it doesn't block a thread) while another credit holds it.
        mutex.withLock {
            balances[account] = (balances[account] ?: 0L) + cents
        }
    }

    suspend fun balance(account: String): Long = mutex.withLock { balances[account] ?: 0L }
}
