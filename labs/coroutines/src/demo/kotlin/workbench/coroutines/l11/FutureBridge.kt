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

/** Kotlin code with a face for Java: the suspend call gets a CompletableFuture twin. */
class SoupKitchen : AutoCloseable {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)

    /** Cooks a pot of [soup] and returns how many bowls it made. */
    suspend fun cook(soup: String): Int {
        try {
            delay(200) // simmering
            return soup.length * 7
        } catch (e: kotlin.coroutines.cancellation.CancellationException) {
            println("  [kotlin] cooking $soup was cancelled")
            throw e
        }
    }

    fun cookAsync(soup: String): CompletableFuture<Int> = scope.future { cook(soup) }

    override fun close() = scope.cancel()
}

/** The neighbour's Java-style future: a pie that takes 500 ms. It reports whether someone cancelled it. */
fun neighboursPie(): CompletableFuture<String> {
    val f = CompletableFuture<String>()
    CompletableFuture.delayedExecutor(500, TimeUnit.MILLISECONDS).execute { f.complete("apple pie ready") }
    return f
}

fun main() = runBlocking {
    println("1. await() on a Java future, then cancel the coroutine:")
    val f1 = neighboursPie()
    launch { f1.await() }.also { delay(100) }.cancelAndJoin()
    println("  future cancelled: ${f1.isCancelled}")

    println("2. asDeferred().await(), then cancel the coroutine:")
    val f2 = neighboursPie()
    launch { f2.asDeferred().await() }.also { delay(100) }.cancelAndJoin()
    println("  future cancelled: ${f2.isCancelled}  (it still completes: ${f2.get()})")

    println("3. future { } for a Java caller, who cancels it:")
    SoupKitchen().use { kitchen ->
        val f3 = kitchen.cookAsync("leek")
        delay(50)
        f3.cancel(true)
        delay(50)
        println("  future cancelled: ${f3.isCancelled}")
    }
}
