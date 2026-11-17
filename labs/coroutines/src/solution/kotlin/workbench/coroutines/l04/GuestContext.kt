package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.withContext

suspend fun <T> withGuest(guest: String, block: suspend CoroutineScope.() -> T): T =
    // + combines elements; for the same key, the right-hand side wins over the current context
    withContext(ForGuest(guest) + CoroutineName("for-$guest"), block)

// the companion object ForGuest is the key, so context[ForGuest] returns a ForGuest?
suspend fun currentGuest(): String? = currentCoroutineContext()[ForGuest]?.name
