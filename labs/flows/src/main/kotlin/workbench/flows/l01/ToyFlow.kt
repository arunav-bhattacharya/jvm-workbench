package workbench.flows.l01

import kotlin.coroutines.cancellation.CancellationException

// A flow from scratch. Two interfaces, a builder and four operators, with no kotlinx.coroutines types.
// The interfaces and ToyAbortException are given. Write the five functions below them.

/** The receiving end: one suspend function. kotlinx.coroutines' FlowCollector has the same shape. */
fun interface ToyCollector<in T> {
    suspend fun emit(value: T)
}

/** The sending end: one suspend function that pushes every value into [collector]. Flow has the same shape. */
interface ToyFlow<out T> {
    suspend fun collect(collector: ToyCollector<T>)
}

/**
 * Thrown by [take]'s collector to stop the producer. [owner] names the take that threw it, so that a
 * take further up the chain lets it fly past. Given: you don't need to change it.
 */
class ToyAbortException(val owner: Any) : CancellationException("Toy flow aborted, no more elements needed")

/**
 * Builds a toy flow whose collect runs [block] with the collector as its receiver.
 *
 * Building must run nothing. Every call to collect runs the block again from the top.
 */
fun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    TODO("an object : ToyFlow<T> whose collect calls collector.block()")

/**
 * Every value passed through [transform], in order. The transform and the downstream collector
 * must run inside the upstream's emit call: no list, no queue.
 */
fun <T, R> ToyFlow<T>.map(transform: suspend (T) -> R): ToyFlow<R> =
    TODO("a toyFlow that collects this flow and emits transform(value)")

/** Only the values for which [predicate] is true, in order, inside the upstream's emit call. */
fun <T> ToyFlow<T>.filter(predicate: suspend (T) -> Boolean): ToyFlow<T> =
    TODO("a toyFlow that collects this flow and emits the values that pass")

/**
 * The first [count] values, then the producer stops.
 *
 * After the count-th value has gone downstream, throw a [ToyAbortException] carrying a marker object
 * that belongs to this take. It flies back up through the producer's emit, so the producer stops and
 * its finally blocks run. Catch it around the upstream collect, but only if the marker is yours:
 * an abort from another take must keep going. Reject count <= 0 with IllegalArgumentException.
 */
fun <T> ToyFlow<T>.take(count: Int): ToyFlow<T> =
    TODO("require(count > 0), then a toyFlow that counts, emits, and aborts with its own marker")

/** Collects every value into a list, in order. */
suspend fun <T> ToyFlow<T>.toList(): List<T> =
    TODO("collect into a mutable list and return it")
