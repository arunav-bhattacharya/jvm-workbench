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
        val corner = async { delay(300); "corner bakery: one rye loaf left" }
        val market = async { delay(120); "market bakery: plenty of sourdough" }
        val result = select {
            corner.onAwait { it }
            market.onAwait { it }
            onTimeout(budgetMs) { "nobody answered within $budgetMs ms: we bake our own bread" }
        }
        corner.cancel(); market.cancel() // hang up on the others
        result
    }
    println("after ${ms()} ms: $answer")
}
