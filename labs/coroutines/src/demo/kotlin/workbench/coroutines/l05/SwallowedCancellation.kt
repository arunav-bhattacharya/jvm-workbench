package workbench.coroutines.l05

import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.coroutines.cancellation.CancellationException

/** Phones the butcher 20 times, 100 ms apart, to ask if the order is ready. A failed call is logged and tried again. */
suspend fun phoneButcher(rethrowCancellation: Boolean, onCall: () -> Unit) {
    repeat(20) {
        runCatching {
            onCall()     // the phone call to the butcher would go here
            delay(100)
        }.onFailure { e ->
            if (rethrowCancellation && e is CancellationException) throw e
            // swallowed: logged as a "failed call", and the loop goes round again
        }
    }
}

fun main(args: Array<String>) = runBlocking {
    val fixed = args.firstOrNull() == "fixed"
    var calls = 0
    var cancelledAt = -1
    val caller = launch { phoneButcher(rethrowCancellation = fixed) { calls++ } }
    delay(250)
    cancelledAt = calls
    val asked = System.nanoTime()
    caller.cancelAndJoin()
    val ms = (System.nanoTime() - asked) / 1_000_000
    println(if (fixed) "runCatching + rethrow:" else "runCatching, swallowing:")
    println("  calls before cancel: $cancelledAt, after cancel: ${calls - cancelledAt}, cancelAndJoin took $ms ms")
}
