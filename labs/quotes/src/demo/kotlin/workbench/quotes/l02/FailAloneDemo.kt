package workbench.quotes.l02

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Deferred
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.ensureActive
import kotlinx.coroutines.supervisorScope
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withTimeout
import java.io.IOException
import kotlin.coroutines.cancellation.CancellationException

// northbank fails at 50 ms; fjord's own HTTP client gives up at 100 ms; eastgate answers at 300 ms
private suspend fun northbank(): String { delay(50); throw IOException("northbank 503") }
private suspend fun fjord(): String = withTimeout(100) { delay(1_000); "fjord 1.0843" }
private suspend fun eastgate(): String { delay(300); return "eastgate 1.0841" }

private fun CoroutineScope.callAll(): List<Deferred<String>> = listOf(async { northbank() }, async { fjord() }, async { eastgate() })

private suspend fun Deferred<String>.naive(): String? =
    try { await() } catch (e: CancellationException) { throw e } catch (e: Exception) { null }

private suspend fun Deferred<String>.careful(): String? =
    try { await() } catch (e: CancellationException) { currentCoroutineContext().ensureActive(); null } catch (e: Exception) { null }

private suspend fun TestScope.attempt(what: String, block: suspend () -> List<String?>) {
    val t0 = currentTime
    val outcome = try { "answers ${block()}" } catch (e: Exception) { "failed: ${e::class.simpleName}: ${e.message?.substringBefore(" of ")}" }
    println("%-40s at %3d ms  %s".format(what, currentTime - t0, outcome))
}

/** The same three calls in three scopes: who survives a failure, and who survives a timeout? */
fun main() = runTest {
    attempt("coroutineScope, awaitAll") { coroutineScope { callAll().map { it.await() } } }
    attempt("supervisorScope, rethrow every cancel") { supervisorScope { callAll().map { it.naive() } } }
    attempt("supervisorScope, rethrow only our cancel") { supervisorScope { callAll().map { it.careful() } } }
}
