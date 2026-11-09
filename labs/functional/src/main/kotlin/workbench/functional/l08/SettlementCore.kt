package workbench.functional.l08

import java.time.LocalDate

/**
 * The functional core: decides today's settlement from plain values. No clock, no store, no API,
 * no println. The same arguments must always give an equal plan. The rules, from LegacySettlementJob:
 * - refunded payments are skipped;
 * - a payment whose merchant isn't in [merchants] goes to unknownMerchants;
 * - a payment is due when capturedOn + holdDays is not after [today]; otherwise it goes to held;
 * - due payments are summed per merchant into one Payout: fee = gross * feeRate, rounded HALF_EVEN
 *   to 2 decimals, and net = gross - fee. Payouts are ordered by merchant id.
 */
fun planSettlement(payments: List<Payment>, merchants: Map<String, Merchant>, today: LocalDate): SettlementPlan =
    TODO("filterNot, partition, groupBy and sumOf, as in the collections lesson")

/**
 * Returns a new Ledger with two entries per payout, in payout order: Entry("payout:<merchantId>", net, ref),
 * then Entry("fee-income", fee, ref). The receiver is not changed.
 */
fun Ledger.posting(payouts: List<Payout>, ref: String): Ledger =
    TODO("copy(entries = entries.addingAll(...))")
