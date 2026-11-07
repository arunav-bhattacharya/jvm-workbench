package workbench.coroutines.l05

/** The issuer's hold API. Both calls go over the network, so both suspend. */
interface HoldApi {
    suspend fun place(amountCents: Long): String
    suspend fun release(holdId: String)
}

/**
 * Places a hold for [amountCents], runs [block] with the hold id, and always releases
 * the hold afterwards: when the block returns, when it throws, and when the caller is
 * cancelled.
 *
 * Bug: when the caller is cancelled, release() is called from a cancelled coroutine, so
 * its first suspension throws CancellationException and the hold stays on the card.
 */
suspend fun <T> withCardHold(holds: HoldApi, amountCents: Long, block: suspend (holdId: String) -> T): T {
    val holdId = holds.place(amountCents)
    try {
        return block(holdId)
    } finally {
        holds.release(holdId)
    }
}
