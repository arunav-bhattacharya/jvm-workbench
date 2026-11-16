package workbench.flows.l02

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.FlowCollector
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlin.coroutines.EmptyCoroutineContext

/** Collects [f] and prints what happened: the values, or the exception's class and full message. */
suspend fun attempt(name: String, f: Flow<Int>) {
    try {
        f.collect { println("  [$name] collected $it") }
        println("[$name] OK")
    } catch (e: Throwable) {
        println("[$name] ${e::class.qualifiedName}:\n${e.message}\n")
    }
}

/** A Flow written by hand, with no checks: it emits from an IO thread. */
val raw: Flow<String> = object : Flow<String> {
    override suspend fun collect(collector: FlowCollector<String>) {
        withContext(Dispatchers.IO) { collector.emit("from a raw Flow") }
    }
}

fun main() = runBlocking(CoroutineName("collector")) {
    val printer = FlowCollector<String> { v -> println("printer got '$v' on ${Thread.currentThread().name}") }
    raw.collect(printer)

    attempt("withContext(IO)", flow { withContext(Dispatchers.IO) { emit(1) } })
    attempt("withContext(CoroutineName)", flow { withContext(CoroutineName("other")) { emit(1) } })
    attempt("withContext(Empty)", flow { withContext(EmptyCoroutineContext) { emit(1) } })
    attempt("coroutineScope", flow { coroutineScope { emit(1) } })
}
