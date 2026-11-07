package workbench.quotes.l03

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest

/** 40 requests at once to a provider that answers in 50 ms. How many calls does it see at once? */
fun main() = runTest {                                   // virtual time, one thread: plain counters are safe here
    for (limit in listOf(null, 4)) {
        val permits = limit?.let { Semaphore(it) }
        var active = 0
        var peak = 0
        suspend fun call() {
            active++
            peak = maxOf(peak, active)
            delay(50)                                    // the provider thinks
            active--
        }
        val t0 = currentTime
        coroutineScope {
            repeat(40) { launch { if (permits == null) call() else permits.withPermit { call() } } }
        }
        println("%-9s calls in flight at most: %2d   all 40 answered after %3d ms".format(
            if (limit == null) "no limit" else "limit $limit", peak, currentTime - t0))
    }
}
