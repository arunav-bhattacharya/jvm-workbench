package workbench.flows.l01

import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking

/** Prints the call stack from inside a collector, newest frame first, down to the coroutine machinery. */
fun printStack(label: String) {
    println("$label, thread=${Thread.currentThread().name}")
    Thread.currentThread().stackTrace
        .drop(2)                                                   // getStackTrace and printStack
        .takeWhile { !it.className.startsWith("kotlinx.coroutines.DispatchedTask") }
        .forEach { println("    at ${it.className.removePrefix("workbench.flows.l01.")}.${it.methodName}") }
}

fun main() = runBlocking {
    println("=== the toy flow from ToyFlow.kt")
    toyFlow { emit("pay-1") }.collect { printStack("collector got $it") }

    println("=== kotlinx flow { } with map")
    flow { emit("pay-1") }.map { it.uppercase() }.collect { printStack("collector got $it") }
}
