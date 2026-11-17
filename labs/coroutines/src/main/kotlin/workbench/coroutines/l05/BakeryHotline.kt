package workbench.coroutines.l05

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlin.time.Duration

/** The bakery's old order line. ask() BLOCKS the calling thread until somebody answers. */
fun interface BakeryHotline {
    fun ask(bread: String): String
}

/**
 * Asks the bakery about [bread], giving up after [timeout].
 * Returns the bakery's answer, or null if nobody answered in time.
 *
 * Two bugs:
 * 1. withTimeout throws TimeoutCancellationException instead of returning null.
 * 2. A timeout can't stop a blocking call: the caller still waits for ask() to finish,
 *    and the IO thread stays blocked. The blocked thread must be interrupted.
 */
suspend fun askBakery(hotline: BakeryHotline, bread: String, timeout: Duration): String? =
    withTimeout(timeout) {
        withContext(Dispatchers.IO) { hotline.ask(bread) }
    }
