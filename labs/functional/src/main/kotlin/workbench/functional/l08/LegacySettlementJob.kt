package workbench.functional.l08

import java.math.BigDecimal
import java.math.RoundingMode
import java.time.Clock
import java.time.LocalDate

/**
 * The job as it runs today. It gives the right answers, but the rules, the clock and the I/O are
 * woven together, so the only way to test a fee rule is with a fake store, a fake API and a fixed clock.
 * Read it to find the rules. Don't edit it: SettlementCore.kt and SettlementJob.kt replace it.
 */
class LegacySettlementJob(private val store: PaymentStore, private val payouts: PayoutApi, private val clock: Clock) {
    fun run() {
        val today = LocalDate.now(clock)
        val merchants = store.merchants()
        val totals = mutableMapOf<String, BigDecimal>()
        for (p in store.capturedPayments()) {
            if (p.refunded) continue
            val m = merchants[p.merchantId]
            if (m == null) { println("unknown merchant ${p.merchantId} for ${p.id}"); continue }
            if (p.capturedOn.plusDays(m.holdDays.toLong()).isAfter(today)) { println("holding ${p.id}"); continue }
            totals[p.merchantId] = (totals[p.merchantId] ?: BigDecimal.ZERO) + p.amount
        }
        var ledger = store.loadLedger()
        for ((merchantId, gross) in totals.toSortedMap()) {
            val fee = (gross * merchants.getValue(merchantId).feeRate).setScale(2, RoundingMode.HALF_EVEN)
            val payout = Payout(merchantId, gross, fee, gross - fee)
            payouts.send(payout)
            ledger = Ledger(
                ledger.entries
                    .adding(Entry("payout:$merchantId", payout.net, "settlement-$today"))
                    .adding(Entry("fee-income", fee, "settlement-$today"))
            )
            store.saveLedger(ledger)
        }
    }
}
