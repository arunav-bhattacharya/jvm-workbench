package workbench.coroutines.l05

import kotlinx.coroutines.NonCancellable
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlin.coroutines.cancellation.CancellationException

private suspend fun giveBack(ticket: String) {
    delay(50) // the phone call to the lending desk
    println("  gave back the pan on $ticket")
}

fun main(args: Array<String>) = runBlocking {
    val fixed = args.firstOrNull() == "fixed"
    val jam = launch {
        val ticket = "ticket-7"
        println("  borrowed the jam pan on $ticket")
        try {
            delay(10_000) // waiting for the jam to set
        } finally {
            try {
                if (fixed) withContext(NonCancellable) { giveBack(ticket) }
                else giveBack(ticket)
            } catch (e: CancellationException) {
                println("  giving back failed at once: ${e::class.simpleName}")
                throw e
            }
        }
    }
    delay(100)
    println(if (fixed) "cancel, giveBack inside withContext(NonCancellable):" else "cancel, plain suspend call in finally:")
    jam.cancelAndJoin()
    println("  jam job finished, cancelled = ${jam.isCancelled}")
}
