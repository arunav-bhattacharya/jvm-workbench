package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineScope

/**
 * Runs [block] with a [ForGuest] for [guest] and a CoroutineName of "for-<guest>" added to the
 * current coroutine context. Coroutines started inside [block] inherit both.
 */
suspend fun <T> withGuest(guest: String, block: suspend CoroutineScope.() -> T): T {
    TODO("withContext with two elements combined by +")
}

/** The guest named in the current coroutine context, or null if there is none. */
suspend fun currentGuest(): String? {
    TODO("look the element up by its key")
}
