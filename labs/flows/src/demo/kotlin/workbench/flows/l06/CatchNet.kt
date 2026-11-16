package workbench.flows.l06

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.FlowCollector
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.isActive
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout
import java.io.IOException

// catch, built by hand: remember what the downstream threw, and leave our own job's cancellation alone.
private fun <T> Flow<T>.myCatch(action: suspend FlowCollector<T>.(Throwable) -> Unit): Flow<T> = flow {
    var fromDownstream: Throwable? = null
    try {
        collect { value ->
            try { emit(value) } catch (e: Throwable) { fromDownstream = e; throw e }   // 1. who threw?
        }
    } catch (e: Throwable) {
        if (e === fromDownstream) throw e                                          // 2. not ours: below the net
        if (e is CancellationException && !currentCoroutineContext().isActive) throw e // 3. our job is cancelled
        action(e)                                                                  // 4. an upstream failure
    }
}

private fun describe(e: Throwable?) = e?.let { "${it::class.simpleName}: ${it.message?.lineSequence()?.first()}" } ?: "nothing"

// One FX rate request, five ways for it to end.
private val cases: List<Pair<String, Flow<Double>>> = listOf(
    "provider throws IOException" to flow { emit(0.92); throw IOException("provider reset") },
    "provider throws CancellationException" to flow { emit(0.92); throw CancellationException("provider gave up") },
    "withTimeout inside the provider call" to flow { emit(0.92); withTimeout(50) { delay(100) }; emit(0.93) },
    "the collector's ledger write fails" to flow { emit(0.92); emit(0.93) },
    "the caller's job is cancelled" to flow { emit(0.92); awaitCancellation() },
)

private fun run(label: String, net: String, f: Flow<Double>) {
    var caught: Throwable? = null
    val netted = if (net == "catch") f.catch { caught = it; emit(-1.0) } else f.myCatch { caught = it; emit(-1.0) }
    val got = mutableListOf<Double>()
    var callerSaw: Throwable? = null
    runBlocking {
        val job = launch {
            try {
                netted.collect { got += it; if (label.startsWith("the collector") && it == 0.92) error("ledger write failed") }
            } catch (e: Throwable) { callerSaw = e; if (e !is CancellationException) Unit else throw e }
        }
        if (label.startsWith("the caller")) { delay(10); job.cancel() }
        job.join()
    }
    println("  %-8s got %-12s net caught %-48s caller saw %s".format(net, got, describe(caught), describe(callerSaw)))
}

fun main() {
    for ((label, f) in cases) {
        println("== $label")
        run(label, "catch", f)
        run(label, "myCatch", f)
    }
}
