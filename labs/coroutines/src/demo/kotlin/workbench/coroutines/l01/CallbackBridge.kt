package workbench.coroutines.l01

import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine
import kotlin.system.measureTimeMillis

/** A bakery's ordering library with a callback API. It answers after 1 second, on its own thread. */
class BakerySdk {
    private val pool = Executors.newSingleThreadScheduledExecutor { r -> Thread(r, "bakery-sdk").apply { isDaemon = true } }

    fun order(bread: String, onReady: (String) -> Unit): () -> Unit {
        val task = pool.schedule({ onReady("ticket 17: one $bread") }, 1, TimeUnit.SECONDS)
        return { println("  bakery: order for $bread cancelled"); task.cancel(false) }
    }
}

// Wrapped with suspendCoroutine: works, but cancellation cannot reach it.
suspend fun BakerySdk.orderAwait(bread: String): String = suspendCoroutine { cont ->
    order(bread) { ticket -> cont.resume(ticket) }
}

fun main() = runBlocking {
    val bakery = BakerySdk()
    val took = measureTimeMillis {
        try {
            withTimeout(100) { bakery.orderAwait("sourdough") }
        } catch (e: TimeoutCancellationException) {
            println("  timed out")
        }
    }
    println("withTimeout(100) returned after $took ms")
}
