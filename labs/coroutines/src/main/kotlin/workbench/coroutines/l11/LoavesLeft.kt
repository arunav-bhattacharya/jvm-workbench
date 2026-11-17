package workbench.coroutines.l11

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

/**
 * How many loaves of [bread] the bakery has left, as a suspend function, for Kotlin code that
 * calls the bakery's Java library.
 *
 * Rules: don't block any thread while waiting, and if the calling coroutine is cancelled,
 * cancel the library's future too (the bakery stops counting when its future is cancelled).
 *
 * Bug: get() on an IO thread "doesn't block the caller", but it blocks an IO thread for the
 * whole wait, and a cancelled caller can't stop it: the future is never cancelled.
 */
suspend fun JavaBakery.loavesLeftAwait(bread: String): Int =
    withContext(Dispatchers.IO) { loavesLeft(bread).get() }
