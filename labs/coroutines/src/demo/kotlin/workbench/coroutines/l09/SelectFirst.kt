package workbench.coroutines.l09

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.selects.onTimeout
import kotlinx.coroutines.selects.select

private var t0 = 0L
private fun ms() = (System.nanoTime() - t0) / 1_000_000

@OptIn(ExperimentalCoroutinesApi::class) // onTimeout is experimental
fun main(args: Array<String>) = runBlocking {
    t0 = System.nanoTime()
    val budgetMs = args.firstOrNull()?.toLong() ?: 500
    val answer = coroutineScope {
        val north = async { delay(300); "north: 1.80%" }
        val east = async { delay(120); "east: 2.10%" }
        val result = select {
            north.onAwait { it }
            east.onAwait { it }
            onTimeout(budgetMs) { "no quote within $budgetMs ms: use the default acquirer" }
        }
        north.cancel(); east.cancel() // stop the losers
        result
    }
    println("after ${ms()} ms: $answer")
}
