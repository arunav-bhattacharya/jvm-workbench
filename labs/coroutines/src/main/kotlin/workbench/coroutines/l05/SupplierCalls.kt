package workbench.coroutines.l05

/**
 * Phones each supplier in turn to confirm tomorrow's delivery. A call that fails is logged
 * and skipped, so one busy line doesn't stop the round. Returns the orders whose call failed.
 *
 * Bug: when the caller is cancelled (the dinner is called off), the round doesn't stop.
 * runCatching also catches the CancellationException, so the call in progress is reported
 * as "failed", and every remaining call is started and "fails" at once.
 * Make cancellation end the round, while ordinary failures are still logged and skipped.
 */
suspend fun confirmEach(orders: List<String>, confirm: suspend (order: String) -> Unit): List<String> {
    val failed = mutableListOf<String>()
    for (order in orders) {
        runCatching { confirm(order) }
            .onFailure { e ->
                println("call for $order failed, skipping: $e")
                failed += order
            }
    }
    return failed
}
