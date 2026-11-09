package workbench.functional.l04

// Write each function as one chain of collection operations: no `for`, no `var`.
// Each TODO names the operation that fits. All of them must work on an empty list.

/** TODO 1: every payment of every batch, in order. (flatMap) */
fun allPayments(batches: List<Batch>): List<Payment> = TODO("flatMap")

/** TODO 2: the sum of amounts of SETTLED payments. 0 for none. (filter, sumOf) */
fun settledCents(payments: List<Payment>): Long = TODO("filter, sumOf")

/** TODO 3: the sum of every refund that exists. Most payments have none. (mapNotNull, sum) */
fun refundedCents(payments: List<Payment>): Long = TODO("mapNotNull, sum")

/**
 * TODO 4: for SETTLED payments only, amount minus refund, added up per merchant.
 * Merchants appear in the order they are first seen. (filter, groupBy, mapValues, sumOf)
 */
fun netByMerchant(payments: List<Payment>): Map<String, Long> = TODO("filter, groupBy, mapValues")

/** TODO 5: the ids of FAILED payments, in input order. (filter, map) */
fun failedIds(payments: List<Payment>): List<String> = TODO("filter, map")

/** TODO 6: the SETTLED payment with the biggest amount, or null when nothing settled. (filter, maxByOrNull) */
fun largestSettled(payments: List<Payment>): Payment? = TODO("filter, maxByOrNull")

/**
 * TODO 7: the merchant account balance after the day. Start from [openingCents]; each SETTLED
 * payment adds its amount minus its refund; PENDING and FAILED payments change nothing. (fold)
 */
fun closingBalance(openingCents: Long, payments: List<Payment>): Long = TODO("fold with a when inside")

/**
 * TODO 8: map each id to its payment. associateBy alone would keep the last payment for a repeated id
 * and say nothing. Instead, throw IllegalArgumentException("duplicate payment ids: pay_2, pay_7"):
 * each repeated id once, in the order first seen, joined with ", ". (groupingBy, eachCount, associateBy)
 */
fun indexById(payments: List<Payment>): Map<String, Payment> = TODO("find duplicates first, then associateBy")

/**
 * TODO 9: the whole report for one settlement day, built from the functions above.
 * A day with duplicate payment ids must be refused (call indexById). An empty day is a normal day.
 */
fun settlementReport(batches: List<Batch>): SettlementReport = TODO("allPayments, indexById, then the rest")
