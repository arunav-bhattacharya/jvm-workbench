package workbench.coroutines.l05

import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.withContext

interface HoldApi {
    suspend fun place(amountCents: Long): String
    suspend fun release(holdId: String)
}

suspend fun <T> withCardHold(holds: HoldApi, amountCents: Long, block: suspend (holdId: String) -> T): T {
    val holdId = holds.place(amountCents)
    try {
        return block(holdId)
    } finally {
        // a cancelled coroutine can't suspend: every suspend call throws at once.
        // NonCancellable lets this one cleanup call run to the end. Use it only in finally.
        withContext(NonCancellable) { holds.release(holdId) }
    }
}
