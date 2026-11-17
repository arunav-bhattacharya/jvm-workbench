package workbench.coroutines.l05

import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.withContext

interface LendingDesk {
    suspend fun lend(item: String): String
    suspend fun giveBack(ticket: String)
}

suspend fun <T> withBorrowed(desk: LendingDesk, item: String, block: suspend (ticket: String) -> T): T {
    val ticket = desk.lend(item)
    try {
        return block(ticket)
    } finally {
        // a cancelled coroutine can't suspend: every suspend call throws at once.
        // NonCancellable lets this one cleanup call run to the end. Use it only in finally.
        withContext(NonCancellable) { desk.giveBack(ticket) }
    }
}
