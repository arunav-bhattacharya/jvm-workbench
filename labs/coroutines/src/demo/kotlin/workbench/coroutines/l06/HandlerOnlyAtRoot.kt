package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

fun main() = runBlocking {
    // the kitchen notebook: writes down what went wrong, after the fact
    val handler = CoroutineExceptionHandler { ctx, e -> println("  handler got: ${e.message} (from ${ctx[CoroutineName]?.name})") }

    println("1. handler on a child inside coroutineScope:")
    try {
        coroutineScope {
            launch(handler + CoroutineName("child")) { throw BurnedException("the tray burned") }
        }
    } catch (e: BurnedException) {
        println("  coroutineScope threw: ${e.message}  (the child's handler was ignored)")
    }

    println("2. handler on a scope with a SupervisorJob, root launch:")
    val oven = CoroutineScope(SupervisorJob() + Dispatchers.Default + handler)
    oven.launch(CoroutineName("root-launch")) { throw BurnedException("the tray burned") }.join()

    println("3. the same scope, root async that nobody awaits:")
    val d = oven.async(CoroutineName("root-async")) { throw BurnedException("the tray burned") }
    delay(100)
    println("  nothing printed: the failure waits in the Deferred")
    try { d.await() } catch (e: BurnedException) { println("  await threw: ${e.message}") }
}
