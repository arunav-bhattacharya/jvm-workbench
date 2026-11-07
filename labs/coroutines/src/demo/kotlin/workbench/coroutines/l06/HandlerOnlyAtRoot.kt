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
import java.io.IOException

fun main() = runBlocking {
    val handler = CoroutineExceptionHandler { ctx, e -> println("  handler got: ${e.message} (from ${ctx[CoroutineName]?.name})") }

    println("1. handler on a child inside coroutineScope:")
    try {
        coroutineScope {
            launch(handler + CoroutineName("child")) { throw IOException("webhook 503") }
        }
    } catch (e: IOException) {
        println("  coroutineScope threw: ${e.message}  (the child's handler was ignored)")
    }

    println("2. handler on a scope with a SupervisorJob, root launch:")
    val webhooks = CoroutineScope(SupervisorJob() + Dispatchers.Default + handler)
    webhooks.launch(CoroutineName("root-launch")) { throw IOException("webhook 503") }.join()

    println("3. the same scope, root async that nobody awaits:")
    val d = webhooks.async(CoroutineName("root-async")) { throw IOException("webhook 503") }
    delay(100)
    println("  nothing printed: the failure waits in the Deferred")
    try { d.await() } catch (e: IOException) { println("  await threw: ${e.message}") }
}
