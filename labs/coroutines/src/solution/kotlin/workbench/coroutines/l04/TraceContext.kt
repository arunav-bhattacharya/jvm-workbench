package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.withContext

suspend fun <T> withPaymentTrace(traceId: String, block: suspend CoroutineScope.() -> T): T =
    // + combines elements; for the same key, the right-hand side wins over the current context
    withContext(PaymentTrace(traceId) + CoroutineName("payment-$traceId"), block)

// the companion object PaymentTrace is the key, so context[PaymentTrace] returns a PaymentTrace?
suspend fun currentTraceId(): String? = currentCoroutineContext()[PaymentTrace]?.traceId
