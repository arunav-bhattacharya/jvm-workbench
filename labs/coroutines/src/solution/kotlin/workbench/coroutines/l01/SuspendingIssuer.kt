package workbench.coroutines.l01

import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

suspend fun CardIssuerClient.authorizeAwait(request: AuthRequest): Authorization =
    suspendCancellableCoroutine { cont ->
        // 1. start the request; the SDK returns at once and calls back later on its own thread
        val inFlight = authorize(request, object : AuthCallback {
            // 2. resume the coroutine exactly once, with a value or an exception.
            //    If the coroutine was already cancelled, the continuation ignores this late reply.
            override fun onApproved(auth: Authorization) = cont.resume(auth)
            override fun onFailed(error: Throwable) = cont.resumeWithException(error)
        })
        // 3. if the caller is cancelled while we wait, tell the issuer to drop the request
        cont.invokeOnCancellation { inFlight.cancel() }
    }
