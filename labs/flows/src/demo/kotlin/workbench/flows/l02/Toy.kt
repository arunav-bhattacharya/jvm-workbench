package workbench.flows.l02

// The unchecked toy flow from lesson 1, for comparison with flow { }. TransparencyTrap.kt uses it.

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
