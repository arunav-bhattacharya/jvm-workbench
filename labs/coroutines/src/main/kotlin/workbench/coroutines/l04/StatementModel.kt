package workbench.coroutines.l04

import kotlin.coroutines.AbstractCoroutineContextElement
import kotlin.coroutines.CoroutineContext

// Shared model. This file is the same in src/main and src/solution.

data class LedgerRow(val accountId: String, val amountCents: Long, val description: String)

/** A JDBC-style store: every call BLOCKS the calling thread until Oracle answers. */
interface BlockingStatementStore {
    fun loadRows(accountId: String): List<LedgerRow>
}

/** Pure CPU work: lays out the PDF. Takes tens of milliseconds for a busy account. */
interface StatementRenderer {
    fun render(rows: List<LedgerRow>): ByteArray
}

/** A coroutine context element that carries the trace id of the payment being processed. */
class PaymentTrace(val traceId: String) : AbstractCoroutineContextElement(PaymentTrace) {
    companion object Key : CoroutineContext.Key<PaymentTrace>
    override fun toString() = "PaymentTrace($traceId)"
}
