package workbench.flows.l01

import kotlin.coroutines.cancellation.CancellationException

// Reference answer. Same names and signatures as src/main.

fun interface ToyCollector<in T> {
    suspend fun emit(value: T)
}

interface ToyFlow<out T> {
    suspend fun collect(collector: ToyCollector<T>)
}

class ToyAbortException(val owner: Any) : CancellationException("Toy flow aborted, no more elements needed")

fun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    object : ToyFlow<T> {
        // building only captures the block; collect runs it, once per call
        override suspend fun collect(collector: ToyCollector<T>) = collector.block()
    }

fun <T, R> ToyFlow<T>.map(transform: suspend (T) -> R): ToyFlow<R> =
    // a collector wrapped in a collector: our emit is called from inside the upstream's emit
    toyFlow { this@map.collect { value -> emit(transform(value)) } }

fun <T> ToyFlow<T>.filter(predicate: suspend (T) -> Boolean): ToyFlow<T> =
    toyFlow { this@filter.collect { value -> if (predicate(value)) emit(value) } }

fun <T> ToyFlow<T>.take(count: Int): ToyFlow<T> {
    require(count > 0) { "count must be positive, was $count" }   // checked when the flow is built
    return toyFlow {
        val marker = Any()            // 1. this take's name, to sign its "no more, thanks" note
        var seen = 0
        try {
            this@take.collect { value ->
                emit(value)                                            // 2. pass it down first
                if (++seen == count) throw ToyAbortException(marker)   // 3. enough: stop the producer
            }
        } catch (e: ToyAbortException) {
            if (e.owner !== marker) throw e   // 4. someone else's note: let it fly on
        }
    }
}

suspend fun <T> ToyFlow<T>.toList(): List<T> {
    val out = mutableListOf<T>()
    collect { value -> out += value }
    return out
}
