package workbench.functional.l08

import java.time.Clock

/**
 * The imperative shell: reads, calls the core, then carries out the plan. It holds no business rules.
 * run() must:
 * 1. read today's date from [clock] once, and load the payments and merchants;
 * 2. call planSettlement;
 * 3. send every payout, in plan order;
 * 4. post all payouts to the ledger with the ref "settlement-<today>" and save it ONCE;
 * 5. return the plan.
 */
class SettlementJob(private val store: PaymentStore, private val payouts: PayoutApi, private val clock: Clock) {
    fun run(): SettlementPlan = TODO("read, decide, act")
}
