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

// The bread course: yesterday's loaf goes out first, then a fresh one from the bakery. Five ways for it to end.
private val cases: List<Pair<String, Flow<String>>> = listOf(
    "the bakery call throws IOException" to flow { emit("old loaf"); throw IOException("line dropped") },
    "the bakery call throws CancellationException" to flow { emit("old loaf"); throw CancellationException("bakery gave up") },
    "withTimeout inside the bakery call" to flow { emit("old loaf"); withTimeout(50) { delay(100) }; emit("fresh loaf") },
    "the diner drops a plate" to flow { emit("old loaf"); emit("fresh loaf") },
    "the caller's job is cancelled" to flow { emit("old loaf"); awaitCancellation() },
)

private fun run(label: String, net: String, f: Flow<String>) {
    var caught: Throwable? = null
    val netted = if (net == "catch") f.catch { caught = it; emit("crackers") } else f.myCatch { caught = it; emit("crackers") }
    val got = mutableListOf<String>()
    var callerSaw: Throwable? = null
    runBlocking {
        val job = launch {
            try {
                netted.collect { got += it; if (label.startsWith("the diner") && it == "old loaf") error("the diner dropped the plate") }
            } catch (e: Throwable) { callerSaw = e; if (e !is CancellationException) Unit else throw e }
        }
        if (label.startsWith("the caller")) { delay(10); job.cancel() }
        job.join()
    }
    println("  %-8s got %-22s net caught %-48s caller saw %s".format(net, got, describe(caught), describe(callerSaw)))
}

fun main() {
    for ((label, f) in cases) {
        println("== $label")
        run(label, "catch", f)
        run(label, "myCatch", f)
    }
}
