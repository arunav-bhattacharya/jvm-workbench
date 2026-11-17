package workbench.coroutines.l03

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** A dish that went wrong. */
class BurnedException(message: String) : Exception(message)

/** One child fails at 100 ms. Watch what happens to its sibling and to the caller. */
fun main(args: Array<String>) = runBlocking {
    val roastBurns = args.firstOrNull() != "ok"
    val t0 = System.nanoTime()
    fun log(msg: String) = println("[%4d ms] %s".format((System.nanoTime() - t0) / 1_000_000, msg))
    try {
        coroutineScope {
            launch {
                delay(100)
                if (roastBurns) {
                    log("roast: burned, throwing BurnedException")
                    throw BurnedException("the roast burned")
                }
                log("roast: done")
            }
            launch {
                try {
                    delay(1_000)
                    log("potatoes: done")
                } finally {
                    log("potatoes: finally block runs")
                }
            }
            log("scope body finished; the scope now waits for its children")
        }
        log("coroutineScope returned normally")
    } catch (e: BurnedException) {
        log("caller caught: ${e.message}")
    }
}
