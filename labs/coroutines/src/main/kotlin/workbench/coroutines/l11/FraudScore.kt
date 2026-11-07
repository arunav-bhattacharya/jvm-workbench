package workbench.coroutines.l11

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * The fraud score for [req], as a suspend function, for Kotlin code that calls the Java client.
 *
 * Rules: don't block any thread while waiting, and if the calling coroutine is cancelled,
 * cancel the client's future too (the client stops scoring when its future is cancelled).
 *
 * Bug: get() on an IO thread "doesn't block the caller", but it blocks an IO thread for the
 * whole wait, and a cancelled caller can't stop it: the future is never cancelled.
 */
suspend fun LegacyFraudClient.scoreAwait(req: AuthRequest): Int =
    withContext(Dispatchers.IO) { score(req).get() }
