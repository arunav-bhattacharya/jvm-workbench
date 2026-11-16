package workbench.flows.l02

import kotlin.coroutines.CoroutineContext

// The inspector at the hatch. flow { } wraps every collector in a SafeCollector that checks each emit.
// Here you write a small version of it for the toy flow from lesson 1.

/** Given: the toy collector from lesson 1. */
fun interface ToyCollector<in T> {
    suspend fun emit(value: T)
}

/** Given: the toy flow from lesson 1. */
interface ToyFlow<out T> {
    suspend fun collect(collector: ToyCollector<T>)
}

/** Given: lesson 1's builder. It checks nothing, like the library's internal unsafeFlow. */
fun <T> toyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    object : ToyFlow<T> {
        override suspend fun collect(collector: ToyCollector<T>) = collector.block()
    }

/**
 * Wraps [downstream] and checks every emit, like kotlinx.coroutines' SafeCollector.
 * [collectContext] is the context of the coroutine that called collect.
 *
 * On every emit, in this order:
 * 1. The emitting coroutine must still be active: call ensureActive() on currentCoroutineContext().
 * 2. If an earlier downstream.emit threw, refuse: throw IllegalStateException with a message that
 *    starts with "Flow exception transparency is violated" and includes the earlier exception
 *    (its toString() is enough) and the value you were asked to emit.
 * 3. The emitting context must match [collectContext]: every element except the Job must be the
 *    very same object (===) as the collect context's element with the same key, and both contexts
 *    must have the same number of elements. If not, throw IllegalStateException with a message that
 *    starts with "Flow invariant is violated" and shows both contexts.
 * 4. Call downstream.emit(value). If it throws, remember the exception, then rethrow it unchanged.
 */
class SafeToyCollector<T>(
    private val downstream: ToyCollector<T>,
    private val collectContext: CoroutineContext,
) : ToyCollector<T> {
    override suspend fun emit(value: T) {
        TODO("the four steps above: ensureActive, transparency, same context, then emit and remember a failure")
    }
}

/**
 * Like flow { }: each collect wraps the collector in a SafeToyCollector, with the context of the
 * coroutine that is collecting, and runs [block] with the wrapped collector as its receiver.
 */
fun <T> safeToyFlow(block: suspend ToyCollector<T>.() -> Unit): ToyFlow<T> =
    TODO("an object : ToyFlow<T> whose collect builds SafeToyCollector(collector, currentCoroutineContext())")
