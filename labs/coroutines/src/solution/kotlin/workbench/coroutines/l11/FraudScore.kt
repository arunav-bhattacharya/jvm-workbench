package workbench.coroutines.l11

import kotlinx.coroutines.future.await

// await() suspends until the future completes (no thread waits), unwraps its exception, and
// cancels the future if this coroutine is cancelled. Use asDeferred().await() if the future
// must NOT be cancelled with the caller.
suspend fun LegacyFraudClient.scoreAwait(req: AuthRequest): Int = score(req).await()
