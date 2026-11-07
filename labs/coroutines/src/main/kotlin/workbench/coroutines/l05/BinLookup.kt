package workbench.coroutines.l05

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlin.time.Duration

/** A legacy BIN directory client. lookup() BLOCKS the calling thread until it answers. */
fun interface BinDirectory {
    fun lookup(bin: String): String
}

/**
 * Looks up the card brand for [bin], giving up after [timeout].
 * Returns the brand, or null if the directory did not answer in time.
 *
 * Two bugs:
 * 1. withTimeout throws TimeoutCancellationException instead of returning null.
 * 2. A timeout can't stop a blocking call: the caller still waits for lookup() to finish,
 *    and the IO thread stays blocked. The blocked thread must be interrupted.
 */
suspend fun lookupBrand(directory: BinDirectory, bin: String, timeout: Duration): String? =
    withTimeout(timeout) {
        withContext(Dispatchers.IO) { directory.lookup(bin) }
    }
