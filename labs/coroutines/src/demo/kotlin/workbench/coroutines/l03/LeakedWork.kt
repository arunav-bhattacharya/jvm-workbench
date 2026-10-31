package workbench.coroutines.l03

import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

private var start = 0L
private fun ms() = (System.nanoTime() - start) / 1_000_000

private suspend fun refundSteps(id: String) {
    repeat(6) { step ->
        delay(100)
        println("  [${ms()} ms] refund $id: step $step")
    }
}

/** Leaks: the refund belongs to GlobalScope, not to the request that started it. */
@OptIn(DelicateCoroutinesApi::class)
suspend fun startRefundLeaky(id: String) {
    GlobalScope.launch { refundSteps(id) }
}

/** Structured: the refund is a child of the caller. */
suspend fun startRefund(id: String) = coroutineScope {
    launch { refundSteps(id) }
}

fun main(args: Array<String>) = runBlocking {
    val structured = args.firstOrNull() == "fixed"
    start = System.nanoTime()
    val request = launch {
        if (structured) startRefund("r-17") else startRefundLeaky("r-17")
        delay(10_000) // the request goes on to do other things
    }
    delay(250)
    request.cancel()
    println("[${ms()} ms] request cancelled (client gave up)")
    delay(500) // keep the JVM alive a little to see what still runs
    println("[${ms()} ms] main done")
}
