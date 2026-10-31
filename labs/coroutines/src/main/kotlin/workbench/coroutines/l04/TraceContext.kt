package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineScope

/**
 * Runs [block] with a [PaymentTrace] for [traceId] and a CoroutineName of "payment-<traceId>"
 * added to the current coroutine context. Coroutines started inside [block] inherit both.
 */
suspend fun <T> withPaymentTrace(traceId: String, block: suspend CoroutineScope.() -> T): T {
    TODO("withContext with two elements combined by +")
}

/** The trace id in the current coroutine context, or null if there is none. */
suspend fun currentTraceId(): String? {
    TODO("look the element up by its key")
}
