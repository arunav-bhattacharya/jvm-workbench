package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineExceptionHandler
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.supervisorScope
import java.io.IOException

private var started = 0L
private fun log(msg: String) = println("%5d ms  %s".format((System.nanoTime() - started) / 1_000_000, msg))

// supervisorScope installs no handler of its own, so failed launch children need one in the context
private val handler = CoroutineExceptionHandler { _, e -> log("handler: ${e.message}") }

fun main(args: Array<String>) = runBlocking(handler) {
    started = System.nanoTime()
    val supervised = args.firstOrNull() == "supervisor"
    val sendAll: suspend CoroutineScope.() -> Unit = {
        launch { try { delay(300); log("email sent") } finally { log("email: finally") } }
        launch { delay(50); throw IOException("sms gateway down") }
        launch { try { delay(100); log("push sent") } finally { log("push: finally") } }
    }
    try {
        if (supervised) supervisorScope(sendAll) else coroutineScope(sendAll)
        log("scope returned normally")
    } catch (e: IOException) {
        log("caller caught: ${e.message}")
    }
}
