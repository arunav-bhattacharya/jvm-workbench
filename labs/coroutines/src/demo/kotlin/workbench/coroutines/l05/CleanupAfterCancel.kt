package workbench.coroutines.l05

import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlin.coroutines.cancellation.CancellationException

private suspend fun releaseHold(id: String) {
    delay(50) // the network call to the issuer
    println("  released $id")
}

fun main(args: Array<String>) = runBlocking {
    val fixed = args.firstOrNull() == "fixed"
    val payment = launch {
        val hold = "hold-4250"
        println("  placed $hold")
        try {
            delay(10_000) // waiting for the customer's 3-D Secure challenge
        } finally {
            try {
                if (fixed) withContext(NonCancellable) { releaseHold(hold) }
                else releaseHold(hold)
            } catch (e: CancellationException) {
                println("  release failed at once: ${e::class.simpleName}")
                throw e
            }
        }
    }
    delay(100)
    println(if (fixed) "cancel, release inside withContext(NonCancellable):" else "cancel, plain suspend call in finally:")
    payment.cancelAndJoin()
    println("  payment job finished, cancelled = ${payment.isCancelled}")
}
