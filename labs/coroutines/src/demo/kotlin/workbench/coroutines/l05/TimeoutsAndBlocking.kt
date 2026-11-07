package workbench.coroutines.l05

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.runInterruptible
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.withTimeoutOrNull

/** Runs [block] and prints what came out and how long it took. */
private suspend fun timed(label: String, block: suspend () -> Any?) {
    val t0 = System.nanoTime()
    val outcome = try {
        "returned ${block()}"
    } catch (e: TimeoutCancellationException) {
        "threw TimeoutCancellationException"
    }
    println("%-46s %-36s after %5d ms".format(label, outcome, (System.nanoTime() - t0) / 1_000_000))
}

fun main() = runBlocking {
    // the issuer takes 1.5 s; we give it 300 ms
    timed("withTimeout { delay }") { withTimeout(300) { delay(1_500); "approved" } }
    timed("withTimeoutOrNull { delay }") { withTimeoutOrNull(300) { delay(1_500); "approved" } }
    timed("withTimeout { withContext(IO) { sleep } }") {
        withTimeout(300) { withContext(Dispatchers.IO) { Thread.sleep(1_500); "approved" } }
    }
    timed("withTimeoutOrNull { runInterruptible { sleep } }") {
        withTimeoutOrNull(300) { runInterruptible(Dispatchers.IO) { Thread.sleep(1_500); "approved" } }
    }
}
