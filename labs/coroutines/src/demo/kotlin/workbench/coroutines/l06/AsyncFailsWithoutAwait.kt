package workbench.coroutines.l06

import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.supervisorScope
import java.io.IOException

private var t0 = 0L
private fun log(msg: String) = println("%5d ms  %s".format((System.nanoTime() - t0) / 1_000_000, msg))

fun main(args: Array<String>) = runBlocking {
    t0 = System.nanoTime()
    val supervised = args.firstOrNull() == "supervisor"
    try {
        val body: suspend CoroutineScope.() -> Unit = {
            val risk = async { delay(100); throw IOException("risk service down") }  // nobody awaits this yet
            launch {
                try { delay(1_000); log("ledger: done") } finally { log("ledger: finally") }
            }
            delay(500)
            log("body: still running at 500 ms, about to await risk")
            risk.await()
        }
        if (supervised) supervisorScope(body) else coroutineScope(body)
        log("scope returned normally")
    } catch (e: IOException) {
        log("caller caught: ${e.message}")
    }
}
