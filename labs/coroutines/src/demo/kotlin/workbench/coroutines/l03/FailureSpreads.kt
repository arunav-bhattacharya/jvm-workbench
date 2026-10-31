package workbench.coroutines.l03

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import java.io.IOException

/** One child fails at 100 ms. Watch what happens to its sibling and to the caller. */
fun main(args: Array<String>) = runBlocking {
    val ledgerFails = args.firstOrNull() != "ok"
    val t0 = System.nanoTime()
    fun log(msg: String) = println("[%4d ms] %s".format((System.nanoTime() - t0) / 1_000_000, msg))
    try {
        coroutineScope {
            launch {
                delay(100)
                if (ledgerFails) {
                    log("ledger: throwing IOException")
                    throw IOException("ledger unavailable")
                }
                log("ledger: done")
            }
            launch {
                try {
                    delay(1_000)
                    log("risk: done")
                } finally {
                    log("risk: finally block runs")
                }
            }
            log("scope body finished; the scope now waits for its children")
        }
        log("coroutineScope returned normally")
    } catch (e: IOException) {
        log("caller caught: ${e.message}")
    }
}
