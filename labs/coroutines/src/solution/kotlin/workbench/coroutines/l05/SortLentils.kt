package workbench.coroutines.l05

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive

suspend fun countStones(lentils: LongArray, isStone: (Long) -> Boolean): Int {
    val context = currentCoroutineContext()
    var stones = 0
    for ((i, lentil) in lentils.withIndex()) {
        // a CPU loop has no suspension points, so it must look at its job itself.
        // ensureActive() throws CancellationException once the job is cancelled.
        if (i % 1_000 == 0) context.ensureActive()
        if (isStone(lentil)) stones++
    }
    return stones
}
