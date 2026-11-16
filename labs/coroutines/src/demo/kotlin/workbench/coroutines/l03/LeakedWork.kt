package workbench.coroutines.l03

import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

private var start = 0L
private fun ms() = (System.nanoTime() - start) / 1_000_000

private suspend fun simmerStock(pot: String) {
    repeat(6) { step ->
        delay(100)
        println("  [${ms()} ms] $pot: still simmering, step $step")
    }
}

/** Leaks: the stock belongs to GlobalScope, not to the dinner that started it. */
@OptIn(DelicateCoroutinesApi::class)
suspend fun startStockLeaky(pot: String) {
    GlobalScope.launch { simmerStock(pot) }
}

/** Structured: the stock is a child of the caller. */
suspend fun startStock(pot: String) = coroutineScope {
    launch { simmerStock(pot) }
}

fun main(args: Array<String>) = runBlocking {
    val structured = args.firstOrNull() == "fixed"
    start = System.nanoTime()
    val dinner = launch {
        if (structured) startStock("stock pot") else startStockLeaky("stock pot")
        delay(10_000) // the dinner goes on with other dishes
    }
    delay(250)
    dinner.cancel()
    println("[${ms()} ms] dinner cancelled (the guests called it off)")
    delay(500) // keep the JVM alive a little to see what still runs
    println("[${ms()} ms] main done")
}
