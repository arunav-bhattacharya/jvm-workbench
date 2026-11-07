package workbench.quotes.l03

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withTimeoutOrNull

/**
 * A burst of 500 requests. The provider takes 10 calls at a time, 50 ms each, and every request
 * has a 300 ms deadline. Queue them all, or shed what can't make the deadline?
 */
fun main() = runTest {
    for (maxInFlight in listOf(null, 50)) {
        val provider = Semaphore(10)
        val admission = maxInFlight?.let { Semaphore(it) }
        var live = 0
        var late = 0
        var busy = 0
        var waitedForNothing = 0L
        coroutineScope {
            repeat(500) {
                launch {
                    if (admission != null && !admission.tryAcquire()) {
                        busy++                                       // answered "ERR busy" at once
                        return@launch
                    }
                    try {
                        val start = currentTime
                        val answer = withTimeoutOrNull(300) { provider.withPermit { delay(50) } }
                        if (answer != null) live++ else { late++; waitedForNothing += currentTime - start }
                    } finally {
                        admission?.release()
                    }
                }
            }
        }
        println("%-14s live answers: %3d   missed the deadline: %3d   shed as busy: %3d   ms spent waiting for nothing: %,d".format(
            if (maxInFlight == null) "queue them all" else "admit $maxInFlight", live, late, busy, waitedForNothing))
    }
}
