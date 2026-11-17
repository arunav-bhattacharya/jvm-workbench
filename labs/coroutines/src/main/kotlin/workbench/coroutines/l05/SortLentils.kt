package workbench.coroutines.l05

/**
 * Counts the lentils that [isStone] says are really small stones. Picking through a big sack is
 * pure CPU work, and the kitchen runs it on Dispatchers.Default over millions of lentils.
 *
 * Bug: the loop never looks at its job, so calling the sorting off does nothing until the
 * whole sack is done. Make it stop soon after it is cancelled: check for cancellation at
 * least once every 1,000 lentils. Keep the result the same when nobody cancels.
 */
suspend fun countStones(lentils: LongArray, isStone: (Long) -> Boolean): Int {
    var stones = 0
    for (lentil in lentils) {
        if (isStone(lentil)) stones++
    }
    return stones
}
