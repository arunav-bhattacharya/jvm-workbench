package workbench.coroutines.l05

import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.coroutines.cancellation.CancellationException

/** Polls a settlement 20 times, 100 ms apart. A failed poll is logged and retried. */
suspend fun pollSettlement(rethrowCancellation: Boolean, onAttempt: () -> Unit) {
    repeat(20) {
        runCatching {
            onAttempt()  // the HTTP call to the acquirer would go here
            delay(100)
        }.onFailure { e ->
            if (rethrowCancellation && e is CancellationException) throw e
            // swallowed: logged as a "failed poll", and the loop goes round again
        }
    }
}

fun main(args: Array<String>) = runBlocking {
    val fixed = args.firstOrNull() == "fixed"
    var attempts = 0
    var cancelledAt = -1
    val poller = launch { pollSettlement(rethrowCancellation = fixed) { attempts++ } }
    delay(250)
    cancelledAt = attempts
    val asked = System.nanoTime()
    poller.cancelAndJoin()
    val ms = (System.nanoTime() - asked) / 1_000_000
    println(if (fixed) "runCatching + rethrow:" else "runCatching, swallowing:")
    println("  attempts before cancel: $cancelledAt, after cancel: ${attempts - cancelledAt}, cancelAndJoin took $ms ms")
}
