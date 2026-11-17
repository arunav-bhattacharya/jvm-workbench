@file:OptIn(FlowPreview::class)

package workbench.flows.l06

import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.Job
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.emitAll
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.launchIn
import kotlinx.coroutines.flow.retryWhen
import kotlinx.coroutines.flow.single
import kotlinx.coroutines.flow.timeout
import kotlinx.coroutines.isActive
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestCoroutineScheduler
import kotlinx.coroutines.test.runTest
import java.io.IOException
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

@OptIn(kotlinx.coroutines.ExperimentalCoroutinesApi::class)
private suspend fun now() = currentCoroutineContext()[TestCoroutineScheduler]!!.currentTime
private suspend fun log(msg: String) = println("%5d ms  %s".format(now(), msg))

/** script(n) says what call n does: a latency in ms, or an exception thrown after 20 ms. */
private class Bakery(val name: String, val script: (Int) -> Any) {
    var calls = 0
    fun order(kind: String): Flow<String> = flow {
        val n = ++calls
        log("    $name call $n starts")
        when (val step = script(n)) {
            is Long -> { delay(step); emit("$kind from $name") }
            is Throwable -> { delay(20); throw step }
        }
    }
}

private fun transient(e: Throwable) = e is IOException || e is TimeoutCancellationException

private fun <T> Flow<T>.backoff(max: Long = 3, first: Duration = 100.milliseconds): Flow<T> = retryWhen { cause, attempt ->
    if (attempt >= max || !transient(cause)) return@retryWhen false
    val wait = first * (1L shl attempt.toInt()).toDouble()
    log("    retry ${attempt + 1} after ${cause::class.simpleName}, waiting $wait")
    delay(wait)
    true
}

private fun case(title: String, bakery: Bakery, backup: Bakery, budget: Duration? = null) = runTest {
    println("== $title")
    var f = bakery.order("sourdough").timeout(300.milliseconds).backoff()
    if (budget != null) f = f.timeout(budget)
    val loaf = f.catch { e ->
        if (!transient(e)) throw e
        log("    the corner bakery gave up (${e::class.simpleName}: ${e.message}); calling the backup")
        emitAll(backup.order("sourdough"))
    }
    val outcome = runCatching { loaf.single() }.fold({ "result: $it" }, { "caller saw ${it::class.simpleName}: ${it.message}" })
    log("  $outcome  (corner calls ${bakery.calls}, backup calls ${backup.calls})")
}

class BakeryTimeout(cause: Throwable) : Exception("the bakery timed out", cause)

fun main() {
    case("A: two dropped calls, then a 50 ms answer", Bakery("corner") { n -> if (n <= 2) IOException("line dropped") else 50L }, Bakery("backup") { 30L })
    case("B: the corner bakery always takes 1000 ms", Bakery("corner") { 1_000L }, Bakery("backup") { 30L })
    case("C: a bread nobody bakes is not transient", Bakery("corner") { IllegalArgumentException("nobody bakes moon bread") }, Bakery("backup") { 30L })
    case("D: both bakeries closed", Bakery("corner") { IOException("corner bakery closed") }, Bakery("backup") { IOException("backup bakery closed") })
    case("E: B again, with timeout(1s) as an overall budget", Bakery("corner") { 1_000L }, Bakery("backup") { 30L }, budget = 1.seconds)

    println("== a timeout that escapes launchIn is a cancellation: nobody hears it")
    runTest {
        val handler = CoroutineExceptionHandler { _, e -> println("  handler got ${e::class.simpleName}: ${e.message}") }
        val scope = CoroutineScope(Job() + handler + StandardTestDispatcher(testScheduler))
        val silent = flow { delay(200); emit(1) }.timeout(50.milliseconds).launchIn(scope)
        silent.join()
        println("  silent: job cancelled=${silent.isCancelled}, scope active=${scope.isActive}")
        val loud = flow { delay(200); emit(1) }.timeout(50.milliseconds)
            .catch { e -> if (e is TimeoutCancellationException) throw BakeryTimeout(e) else throw e }
            .launchIn(scope)
        loud.join()
        println("  loud: job cancelled=${loud.isCancelled}, scope active=${scope.isActive}")
    }
}
