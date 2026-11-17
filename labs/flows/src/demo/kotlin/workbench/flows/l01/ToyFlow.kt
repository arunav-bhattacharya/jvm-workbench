package workbench.flows.l01

import kotlinx.coroutines.runBlocking

// A flow from scratch: two interfaces and a three-line builder. No kotlinx.coroutines flow types.
// StackDemo.kt and Backpressure.kt in this folder use these too.

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

/** map is a collector wrapped in a collector. */
fun <T, R> ToyFlow<T>.map(transform: suspend (T) -> R): ToyFlow<R> =
    toyFlow { this@map.collect { value -> emit(transform(value)) } }

fun main() = runBlocking {
    val dishes = toyFlow {
        println("  [producer] start")
        for (id in 1..3) {
            println("  [producer] before emit($id)")
            emit(id)
            println("  [producer] after emit($id)")
        }
        println("  [producer] done")
    }
    println("built the flow, nothing ran yet")

    println("--- first collect, through map")
    dishes.map { it * 100 }.collect { v -> println("  [collector] got $v") }

    println("--- second collect: the body runs again")
    dishes.collect { v -> println("  [collector] got $v") }
}
