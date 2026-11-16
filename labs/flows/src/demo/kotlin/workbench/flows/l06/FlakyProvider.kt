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
private class Provider(val name: String, val script: (Int) -> Any) {
    var calls = 0
    fun rate(pair: String): Flow<String> = flow {
        val n = ++calls
        log("    $name call $n starts")
        when (val step = script(n)) {
            is Long -> { delay(step); emit("$pair 0.92 from $name") }
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

private fun case(title: String, primary: Provider, fallback: Provider, budget: Duration? = null) = runTest {
    println("== $title")
    var f = primary.rate("USD/EUR").timeout(300.milliseconds).backoff()
    if (budget != null) f = f.timeout(budget)
    val rate = f.catch { e ->
        if (!transient(e)) throw e
        log("    primary gave up (${e::class.simpleName}: ${e.message}); using the fallback")
        emitAll(fallback.rate("USD/EUR"))
    }
    val outcome = runCatching { rate.single() }.fold({ "result: $it" }, { "caller saw ${it::class.simpleName}: ${it.message}" })
    log("  $outcome  (primary calls ${primary.calls}, fallback calls ${fallback.calls})")
}

class ProviderTimeout(cause: Throwable) : Exception("FX provider timed out", cause)

fun main() {
    case("A: two resets, then a 50 ms answer", Provider("primary") { n -> if (n <= 2) IOException("reset") else 50L }, Provider("fallback") { 30L })
    case("B: the primary always takes 1000 ms", Provider("primary") { 1_000L }, Provider("fallback") { 30L })
    case("C: a bad pair is not transient", Provider("primary") { IllegalArgumentException("unsupported pair") }, Provider("fallback") { 30L })
    case("D: both providers down", Provider("primary") { IOException("primary down") }, Provider("fallback") { IOException("fallback down") })
    case("E: B again, with timeout(1s) as an overall budget", Provider("primary") { 1_000L }, Provider("fallback") { 30L }, budget = 1.seconds)

    println("== a timeout that escapes launchIn is a cancellation: nobody hears it")
    runTest {
        val handler = CoroutineExceptionHandler { _, e -> println("  handler got ${e::class.simpleName}: ${e.message}") }
        val scope = CoroutineScope(Job() + handler + StandardTestDispatcher(testScheduler))
        val silent = flow { delay(200); emit(1) }.timeout(50.milliseconds).launchIn(scope)
        silent.join()
        println("  silent: job cancelled=${silent.isCancelled}, scope active=${scope.isActive}")
        val loud = flow { delay(200); emit(1) }.timeout(50.milliseconds)
            .catch { e -> if (e is TimeoutCancellationException) throw ProviderTimeout(e) else throw e }
            .launchIn(scope)
        loud.join()
        println("  loud: job cancelled=${loud.isCancelled}, scope active=${scope.isActive}")
    }
}
