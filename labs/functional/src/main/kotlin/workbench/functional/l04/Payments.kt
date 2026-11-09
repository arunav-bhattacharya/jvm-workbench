package workbench.functional.l04

enum class Status { SETTLED, PENDING, FAILED }

data class Payment(
    val id: String,
    val merchant: String,
    val amountCents: Long,
    val status: Status,
    val refundCents: Long? = null,      // set when part of a settled payment was refunded
)

/** One file from the acquirer. A settlement day is a list of batches. */
data class Batch(val id: String, val payments: List<Payment>)

data class SettlementReport(
    val paymentCount: Int,              // payments in all batches
    val settledCents: Long,             // sum of amounts of SETTLED payments
    val refundedCents: Long,            // sum of every refund that exists
    val netByMerchant: Map<String, Long>, // SETTLED only: amount minus refund, merchants in first-seen order
    val failedIds: List<String>,        // ids of FAILED payments, in input order
    val largestSettled: Payment?,       // the biggest SETTLED payment, null when there is none
)

/**
 * The report as it was first written: one loop and five mutable accumulators. It is finished and
 * gives the right answer on a normal day. Read it; don't edit it. One test compares your version with it.
 * It also has two bugs that a normal day never shows. The tests for your version find both.
 */
fun settlementReportLoop(batches: List<Batch>): SettlementReport {
    val all = ArrayList<Payment>()
    for (b in batches) for (p in b.payments) all.add(p)
    var settled = 0L
    var refunded = 0L
    val net = LinkedHashMap<String, Long>()
    val failed = ArrayList<String>()
    var largest = all.first()
    for (p in all) {
        if (p.refundCents != null) refunded += p.refundCents
        when (p.status) {
            Status.SETTLED -> {
                settled += p.amountCents
                net[p.merchant] = (net[p.merchant] ?: 0L) + p.amountCents - (p.refundCents ?: 0L)
                if (p.amountCents > largest.amountCents) largest = p
            }
            Status.FAILED -> failed.add(p.id)
            Status.PENDING -> {}
        }
    }
    return SettlementReport(all.size, settled, refunded, net, failed, largest)
}
