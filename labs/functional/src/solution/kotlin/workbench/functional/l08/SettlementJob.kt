package workbench.functional.l08

import java.time.Clock
import java.time.LocalDate

class SettlementJob(private val store: PaymentStore, private val payouts: PayoutApi, private val clock: Clock) {
    fun run(): SettlementPlan {
        val today = LocalDate.now(clock)                                              // 1. read
        val plan = planSettlement(store.capturedPayments(), store.merchants(), today)  // 2. decide
        plan.payouts.forEach(payouts::send)                                           // 3. act
        store.saveLedger(store.loadLedger().posting(plan.payouts, "settlement-$today"))
        return plan
    }
}
