package workbench.functional.l08

import java.math.RoundingMode
import java.time.LocalDate

fun planSettlement(payments: List<Payment>, merchants: Map<String, Merchant>, today: LocalDate): SettlementPlan {
    val live = payments.filterNot { it.refunded }
    val (known, unknown) = live.partition { it.merchantId in merchants }
    val (due, held) = known.partition { p ->
        !p.capturedOn.plusDays(merchants.getValue(p.merchantId).holdDays.toLong()).isAfter(today)
    }
    val payouts = due.groupBy { it.merchantId }
        .toSortedMap()                                         // payouts ordered by merchant id
        .map { (merchantId, ps) ->
            val gross = ps.sumOf { it.amount }                 // the BigDecimal overload of sumOf
            val fee = (gross * merchants.getValue(merchantId).feeRate)
                .setScale(2, RoundingMode.HALF_EVEN)           // scale 2, or 3.63950 != 3.64 in equals
            Payout(merchantId, gross, fee, gross - fee)
        }
    return SettlementPlan(payouts, held.map { it.id }, unknown.map { it.id })
}

fun Ledger.posting(payouts: List<Payout>, ref: String): Ledger =
    copy(entries = entries.addingAll(payouts.flatMap { p ->
        listOf(Entry("payout:${p.merchantId}", p.net, ref), Entry("fee-income", p.fee, ref))
    }))                                                        // a new list; the old one is untouched
