package workbench.coroutines.l05

/**
 * Counts the amounts that [isFlagged] marks as suspicious. A nightly job runs this on
 * Dispatchers.Default over millions of card transactions.
 *
 * Bug: the loop never looks at its job, so cancelling the scan does nothing until the
 * whole array is done. Make it stop soon after it is cancelled: check for cancellation
 * at least once every 1,000 amounts. Keep the result the same when nobody cancels.
 */
suspend fun countFlagged(amounts: LongArray, isFlagged: (Long) -> Boolean): Int {
    var flagged = 0
    for (amount in amounts) {
        if (isFlagged(amount)) flagged++
    }
    return flagged
}
