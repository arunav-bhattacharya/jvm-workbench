package workbench.flows.l02

import kotlinx.coroutines.Job
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.ensureActive
import kotlin.coroutines.CoroutineContext

// Reference answer. Same names and signatures as src/main.

fun interface ToyCollector<in T> {
    suspend fun emit(value: T)
}

interface ToyFlow<out T> {
    suspend fun collect(collector: ToyCollector<T>)
}

fun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    object : ToyFlow<T> {
        override suspend fun collect(collector: ToyCollector<T>) = collector.block()
    }

class SafeToyCollector<T>(
    private val downstream: ToyCollector<T>,
    private val collectContext: CoroutineContext,
) : ToyCollector<T> {
    private var downstreamFailure: Throwable? = null

    override suspend fun emit(value: T) {
        val emitContext = currentCoroutineContext()
        // 1. is the kitchen still open?
        emitContext.ensureActive()
        // 2. did the diner throw the last plate back? Then the hatch stays shut.
        downstreamFailure?.let { earlier ->
            throw IllegalStateException(
                "Flow exception transparency is violated: an earlier emit threw $earlier, " +
                    "but then '$value' was emitted. Use the catch operator instead of a try/catch around emit.",
            )
        }
        // 3. same kitchen and same badge as the collector?
        if (!sameContext(emitContext, collectContext)) {
            throw IllegalStateException(
                "Flow invariant is violated: collected in $collectContext, but emission happened in $emitContext. " +
                    "Use flowOn instead.",
            )
        }
        // 4. hand the plate over; if it comes back as an exception, remember it
        try {
            downstream.emit(value)
        } catch (e: Throwable) {
            downstreamFailure = e
            throw e
        }
    }

    private fun sameContext(emit: CoroutineContext, collect: CoroutineContext): Boolean {
        // every element except the Job must be the very same object (coroutineScope { } only adds a Job)
        val differs = emit.fold(false) { bad, element -> bad || (element.key !== Job && collect[element.key] !== element) }
        val sizes = emit.fold(0) { n, _ -> n + 1 } == collect.fold(0) { n, _ -> n + 1 }
        return !differs && sizes
    }
}

fun <T> safeToyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    object : ToyFlow<T> {
        override suspend fun collect(collector: ToyCollector<T>) {
            // the inspector remembers the context of the coroutine that asked for the values
            SafeToyCollector(collector, currentCoroutineContext()).block()
        }
    }
