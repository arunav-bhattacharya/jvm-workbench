package workbench.coroutines.l01

import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

suspend fun BakeryClient.orderAwait(order: BreadOrder): Pickup =
    suspendCancellableCoroutine { cont ->
        // 1. place the order; the library returns at once and calls back later on its own thread
        val pending = order(order, object : OrderCallback {
            // 2. resume the coroutine exactly once, with a value or an exception.
            //    If the coroutine was already cancelled, the continuation ignores this late reply.
            override fun onReady(pickup: Pickup) = cont.resume(pickup)
            override fun onFailed(error: Throwable) = cont.resumeWithException(error)
        })
        // 3. if the caller is cancelled while we wait, tell the bakery to drop the order
        cont.invokeOnCancellation { pending.cancel() }
    }
