package workbench.coroutines.l01

/**
 * Waits [millis] before phoning the bakery again, after a failed order.
 *
 * It is called from coroutines that share a few threads. This version works, but while one
 * coroutine waits, no other coroutine can use its thread. Make it wait without blocking.
 */
suspend fun pauseBeforeRetry(millis: Long) {
    Thread.sleep(millis)
}
