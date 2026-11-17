package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.supervisorScope

private var started = 0L
private fun log(msg: String) = println("%5d ms  %s".format((System.nanoTime() - started) / 1_000_000, msg))

// supervisorScope installs no handler of its own, so failed launch children need one in the context
private val handler = CoroutineExceptionHandler { _, e -> log("handler: ${e.message}") }

fun main(args: Array<String>) = runBlocking(handler) {
    started = System.nanoTime()
    val supervised = args.firstOrNull() == "supervisor"
    // three trays for the bake sale, all in the oven at once
    val bakeAll: suspend CoroutineScope.() -> Unit = {
        launch { try { delay(300); log("cookies baked") } finally { log("cookies: finally") } }
        launch { delay(50); throw BurnedException("the scones burned") }
        launch { try { delay(100); log("muffins baked") } finally { log("muffins: finally") } }
    }
    try {
        if (supervised) supervisorScope(bakeAll) else coroutineScope(bakeAll)
        log("scope returned normally")
    } catch (e: BurnedException) {
        log("caller caught: ${e.message}")
    }
}
