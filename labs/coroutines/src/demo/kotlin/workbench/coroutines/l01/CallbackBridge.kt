package workbench.coroutines.l01

import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import kotlin.coroutines.resume
import kotlin.coroutines.suspendCoroutine
import kotlin.system.measureTimeMillis

/** A fraud-scoring SDK with a callback API. It answers after 1 second on its own thread. */
class FraudSdk {
    private val pool = Executors.newSingleThreadScheduledExecutor { r -> Thread(r, "fraud-sdk").apply { isDaemon = true } }

    fun score(paymentId: String, onScore: (Int) -> Unit): () -> Unit {
        val task = pool.schedule({ onScore(17) }, 1, TimeUnit.SECONDS)
        return { println("  sdk: request for $paymentId cancelled"); task.cancel(false) }
    }
}

// Wrapped with suspendCoroutine: works, but cancellation cannot reach it.
suspend fun FraudSdk.scoreAwait(paymentId: String): Int = suspendCoroutine { cont ->
    score(paymentId) { s -> cont.resume(s) }
}

fun main() = runBlocking {
    val sdk = FraudSdk()
    val took = measureTimeMillis {
        try {
            withTimeout(100) { sdk.scoreAwait("pay_981") }
        } catch (e: TimeoutCancellationException) {
            println("  timed out")
        }
    }
    println("withTimeout(100) returned after $took ms")
}
