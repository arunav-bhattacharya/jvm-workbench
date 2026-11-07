package workbench.coroutines.l05

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.runInterruptible
import kotlinx.coroutines.withTimeoutOrNull
import kotlin.time.Duration

fun interface BinDirectory {
    fun lookup(bin: String): String
}

suspend fun lookupBrand(directory: BinDirectory, bin: String, timeout: Duration): String? =
    // 1. withTimeoutOrNull returns null on timeout instead of throwing
    withTimeoutOrNull(timeout) {
        // 2. runInterruptible interrupts the blocked IO thread when the coroutine is cancelled,
        //    and turns the InterruptedException back into a CancellationException
        runInterruptible(Dispatchers.IO) { directory.lookup(bin) }
    }
