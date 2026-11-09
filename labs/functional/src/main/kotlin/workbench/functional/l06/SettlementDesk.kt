package workbench.functional.l06

// Four functions from a settlement desk. Each one compiles, reads fine at a glance, and has a bug
// caused by a scope function. The tests describe what each should do. Rewrite each function so it
// says what it means: often with fewer scope functions, sometimes with none.

/**
 * Posts [cached] if we have it. On a cache miss (cached == null), loads the payment with [fetch] and
 * posts that. Returns Posted with the entry id, or AlreadyPosted when the ledger says it was posted before.
 *
 * [fetch] is a query against the payments database: call it only on a cache miss, and post at most once.
 */
fun settle(cached: Payment?, ledger: Ledger, fetch: () -> Payment): SettleResult =
    cached?.let { payment -> ledger.post(payment)?.let { SettleResult.Posted(it) } }
        ?: run {
            val payment = fetch()
            ledger.post(payment)?.let { SettleResult.Posted(it) } ?: SettleResult.AlreadyPosted(payment.id)
        }

/** Returns [payment] marked CAPTURED if it is AUTHORIZED. A payment in any other state comes back unchanged. */
fun capture(payment: Payment): Payment =
    payment.takeIf { it.status == Status.AUTHORIZED }
        ?.also { it.copy(status = Status.CAPTURED) }
        ?: payment

/** Builds the gateway request for [order]: amount and merchant from the order, the order id as the request's reference, channel "ecom". */
fun buildRequest(order: Order): PaymentRequest =
    PaymentRequest().apply {
        amount = order.total
        merchantId = order.merchantId
        metadata.apply {
            channel = "ecom"
            reference = order.id
        }
    }

/** "Acme Books: 290 bps" for a merchant whose fee schedule exists, or "m-7: no fee schedule" when the merchant or the schedule is missing. */
fun feeLabel(merchantId: String, merchants: Map<String, Merchant>, schedules: Map<String, FeeSchedule>): String =
    merchants[merchantId]?.let {
        schedules[it.scheduleId]?.let { "${it.name}: ${it.rateBps} bps" }
    } ?: "$merchantId: no fee schedule"
