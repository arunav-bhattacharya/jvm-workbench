package workbench.functional.l06

fun settle(cached: Payment?, ledger: Ledger, fetch: () -> Payment): SettleResult {
    val payment = cached ?: fetch()                    // fetch only when there is really no cached payment
    val entryId = ledger.post(payment)                 // post exactly once
        ?: return SettleResult.AlreadyPosted(payment.id)
    return SettleResult.Posted(entryId)
}
// The bug: in `cached?.let { A } ?: run { B }`, B runs whenever A's *result* is null, and
// ledger.post returns null for a duplicate. So a cache hit on an already-posted payment fetched and posted again.

fun capture(payment: Payment): Payment =
    if (payment.status == Status.AUTHORIZED) payment.copy(status = Status.CAPTURED)   // return the copy
    else payment
// The bug: also { } takes a (T) -> Unit block, so the copy it made was thrown away, and also returned the original.

fun buildRequest(order: Order): PaymentRequest =
    PaymentRequest().apply {
        amount = order.total
        merchantId = order.merchantId
        reference = order.id                           // set on the request: no inner receiver in the way
        metadata.channel = "ecom"                      // one property needs no nested apply
    }
// The bug: inside metadata.apply { }, an unqualified `reference` means metadata.reference, the innermost receiver.

fun feeLabel(merchantId: String, merchants: Map<String, Merchant>, schedules: Map<String, FeeSchedule>): String {
    val merchant = merchants[merchantId] ?: return "$merchantId: no fee schedule"
    val schedule = schedules[merchant.scheduleId] ?: return "$merchantId: no fee schedule"
    return "${merchant.name}: ${schedule.rateBps} bps"   // two names, no guessing which `it`
}
// The bug: the inner `it` (the schedule) hid the outer `it` (the merchant), so it.name was the schedule's name.
