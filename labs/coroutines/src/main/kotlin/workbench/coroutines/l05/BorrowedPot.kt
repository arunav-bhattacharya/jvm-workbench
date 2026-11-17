package workbench.coroutines.l05

/** The community kitchen's lending desk. Both calls go over the phone, so both suspend. */
interface LendingDesk {
    /** Lends [item] and returns a loan ticket for it. */
    suspend fun lend(item: String): String

    /** Takes the item on [ticket] back. */
    suspend fun giveBack(ticket: String)
}

/**
 * Borrows [item], runs [block] with the loan ticket, and always gives the item back
 * afterwards: when the block returns, when it throws, and when the caller is cancelled.
 *
 * Bug: when the caller is cancelled, giveBack() is called from a cancelled coroutine, so its
 * first suspension throws CancellationException and the pot is never returned.
 */
suspend fun <T> withBorrowed(desk: LendingDesk, item: String, block: suspend (ticket: String) -> T): T {
    val ticket = desk.lend(item)
    try {
        return block(ticket)
    } finally {
        desk.giveBack(ticket)
    }
}
