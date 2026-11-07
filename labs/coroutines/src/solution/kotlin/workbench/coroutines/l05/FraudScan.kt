package workbench.coroutines.l05

import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive

suspend fun countFlagged(amounts: LongArray, isFlagged: (Long) -> Boolean): Int {
    val context = currentCoroutineContext()
    var flagged = 0
    for ((i, amount) in amounts.withIndex()) {
        // a CPU loop has no suspension points, so it must look at its job itself.
        // ensureActive() throws CancellationException once the job is cancelled.
        if (i % 1_000 == 0) context.ensureActive()
        if (isFlagged(amount)) flagged++
    }
    return flagged
}
