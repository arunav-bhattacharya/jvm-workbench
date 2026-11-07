package workbench.coroutines.l10

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/** Converts an amount to euro cents. Calls the FX service, so it suspends. */
fun interface FxConverter {
    suspend fun toEurCents(amount: Long, currency: String): Long
}

/**
 * In-memory balances per account, credited by many coroutines at once.
 *
 * Rules:
 * - Every credit must land: 100 concurrent credits of 1 EUR add exactly 100 EUR.
 * - Conversions (the slow, suspending part) may run at the same time; only the
 *   balance update itself must be one-at-a-time.
 *
 * Bug: limitedParallelism(1) runs one coroutine at a time, but only BETWEEN suspension
 * points. Each credit reads the balance, suspends in toEurCents, and writes later, so
 * credits overwrite each other.
 */
class BalanceBook(private val fx: FxConverter) {
    private val balances = HashMap<String, Long>()
    private val serial = Dispatchers.Default.limitedParallelism(1, "balance-book")

    suspend fun credit(account: String, amount: Long, currency: String) {
        withContext(serial) {
            val before = balances[account] ?: 0L
            val cents = fx.toEurCents(amount, currency) // suspends: another credit runs here
            balances[account] = before + cents
        }
    }

    suspend fun balance(account: String): Long = withContext(serial) { balances[account] ?: 0L }
}
