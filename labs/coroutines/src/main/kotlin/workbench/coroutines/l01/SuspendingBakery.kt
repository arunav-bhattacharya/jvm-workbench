package workbench.coroutines.l01

/**
 * Calls [BakeryClient.order] and suspends until the bakery answers.
 *
 * - Returns the [Pickup] when the bread is ready.
 * - Throws the error the bakery reports (for example [SoldOutException]).
 * - If the calling coroutine is cancelled while it waits, calls [PendingOrder.cancel] on the
 *   order, so the bakery can drop it. A late reply after that must be ignored.
 *
 * Use `suspendCancellableCoroutine`, not `suspendCoroutine`.
 */
suspend fun BakeryClient.orderAwait(order: BreadOrder): Pickup {
    TODO("wrap order(order, callback) with suspendCancellableCoroutine")
}
