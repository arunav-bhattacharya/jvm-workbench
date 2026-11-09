package workbench.functional.l08

import kotlinx.collections.immutable.PersistentList
import java.math.BigDecimal
import java.time.LocalDate

// The types for the settlement job. Every one is a data class of vals holding immutable values.
// You don't need to change this file.

data class Payment(
    val id: String,
    val merchantId: String,
    val amount: BigDecimal,          // in euros, scale 2: BigDecimal("125.50")
    val capturedOn: LocalDate,
    val refunded: Boolean = false,
)

/** [feeRate] is a fraction: 0.029 means 2.9%. Captured money is held for [holdDays] before it is paid out. */
data class Merchant(val id: String, val feeRate: BigDecimal, val holdDays: Int)

data class Payout(val merchantId: String, val gross: BigDecimal, val fee: BigDecimal, val net: BigDecimal)

/** What the job decided to do today. */
data class SettlementPlan(
    val payouts: List<Payout>,           // one per merchant with due payments, ordered by merchant id
    val held: List<String>,              // ids of payments not yet due, in input order
    val unknownMerchants: List<String>,  // ids of payments whose merchant we don't know, in input order
)

data class Entry(val account: String, val amount: BigDecimal, val ref: String)

/** The ledger is a value: posting returns a new Ledger, and the old one stays as it was. */
data class Ledger(val entries: PersistentList<Entry>)

// The shell's dependencies: everything that does I/O.

interface PaymentStore {
    fun capturedPayments(): List<Payment>
    fun merchants(): Map<String, Merchant>
    fun loadLedger(): Ledger
    fun saveLedger(ledger: Ledger)
}

fun interface PayoutApi {
    fun send(payout: Payout)
}
