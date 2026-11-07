package workbench.coroutines.l11

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.future.asDeferred
import kotlinx.coroutines.future.await
import kotlinx.coroutines.future.future
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import java.util.concurrent.CompletableFuture
import java.util.concurrent.TimeUnit

/** Kotlin code with a Java-friendly face: every suspend call gets a CompletableFuture twin. */
class FraudFacade : AutoCloseable {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    suspend fun score(paymentId: String): Int {
        try {
            delay(200) // the fraud model
            return paymentId.length * 7
        } catch (e: kotlin.coroutines.cancellation.CancellationException) {
            println("  [kotlin] scoring $paymentId was cancelled")
            throw e
        }
    }

    fun scoreAsync(paymentId: String): CompletableFuture<Int> = scope.future { score(paymentId) }

    override fun close() = scope.cancel()
}

/** A Java-style future that takes 500 ms, and reports whether someone cancelled it. */
fun slowJavaFuture(): CompletableFuture<String> {
    val f = CompletableFuture<String>()
    CompletableFuture.delayedExecutor(500, TimeUnit.MILLISECONDS).execute { f.complete("limits loaded") }
    return f
}

fun main() = runBlocking {
    println("1. await() on a Java future, then cancel the coroutine:")
    val f1 = slowJavaFuture()
    launch { f1.await() }.also { delay(100) }.cancelAndJoin()
    println("  future cancelled: ${f1.isCancelled}")

    println("2. asDeferred().await(), then cancel the coroutine:")
    val f2 = slowJavaFuture()
    launch { f2.asDeferred().await() }.also { delay(100) }.cancelAndJoin()
    println("  future cancelled: ${f2.isCancelled}  (it still completes: ${f2.get()})")

    println("3. future { } for a Java caller, who cancels it:")
    FraudFacade().use { facade ->
        val f3 = facade.scoreAsync("pay-123")
        delay(50)
        f3.cancel(true)
        delay(50)
        println("  future cancelled: ${f3.isCancelled}")
    }
}
