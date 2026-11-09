package workbench.functional.l04

// Each function is one chain. Every operation here is inline on Iterable, so no lambda objects
// are created; each step does build a new list or map.

fun allPayments(batches: List<Batch>): List<Payment> = batches.flatMap { it.payments }

fun settledCents(payments: List<Payment>): Long =
    payments.filter { it.status == Status.SETTLED }.sumOf { it.amountCents }   // sumOf of nothing is 0

fun refundedCents(payments: List<Payment>): Long =
    payments.mapNotNull { it.refundCents }.sum()          // the nulls disappear, so sum sees only refunds

// groupBy returns a LinkedHashMap in first-seen key order, and mapValues keeps that order.
fun netByMerchant(payments: List<Payment>): Map<String, Long> =
    payments.filter { it.status == Status.SETTLED }
        .groupBy { it.merchant }
        .mapValues { (_, ps) -> ps.sumOf { it.amountCents - (it.refundCents ?: 0L) } }

fun failedIds(payments: List<Payment>): List<String> =
    payments.filter { it.status == Status.FAILED }.map { it.id }

// maxByOrNull returns null on an empty list instead of throwing, and keeps the first of equal maxima.
fun largestSettled(payments: List<Payment>): Payment? =
    payments.filter { it.status == Status.SETTLED }.maxByOrNull { it.amountCents }

// fold is the general loop: the accumulator is the balance, and the lambda is one turn of the loop.
fun closingBalance(openingCents: Long, payments: List<Payment>): Long =
    payments.fold(openingCents) { balance, p ->
        when (p.status) {
            Status.SETTLED -> balance + p.amountCents - (p.refundCents ?: 0L)
            Status.PENDING, Status.FAILED -> balance
        }
    }

// associateBy silently keeps the last value for a repeated key, so look for repeats first.
fun indexById(payments: List<Payment>): Map<String, Payment> {
    val duplicates = payments.groupingBy { it.id }.eachCount().filterValues { it > 1 }.keys
    require(duplicates.isEmpty()) { "duplicate payment ids: ${duplicates.joinToString()}" }
    return payments.associateBy { it.id }
}

fun settlementReport(batches: List<Batch>): SettlementReport {
    val payments = allPayments(batches)
    indexById(payments)                                   // refuse the day before adding anything up
    return SettlementReport(
        paymentCount = payments.size,
        settledCents = settledCents(payments),
        refundedCents = refundedCents(payments),
        netByMerchant = netByMerchant(payments),
        failedIds = failedIds(payments),
        largestSettled = largestSettled(payments),
    )
}
