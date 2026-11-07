package workbench.coroutines.l09

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.produce
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlin.random.Random

@OptIn(ExperimentalCoroutinesApi::class)
fun main(args: Array<String>) = runBlocking {
    val workers = args.firstOrNull()?.toInt() ?: 4
    val t0 = System.nanoTime()
    coroutineScope {
        // 1. one producer: 20 refund ids, sent one at a time
        val refunds = produce { for (i in 1..20) send("refund-$i") }
        // 2. fan-out: each id goes to exactly one worker
        val results = Channel<String>()
        val pool = List(workers) { w ->
            launch {
                for (id in refunds) {
                    delay(Random.nextLong(50, 150)) // the issuer call
                    results.send("$id by worker $w")
                }
            }
        }
        // 3. fan-in: close results when every worker is done
        launch { pool.joinAll(); results.close() }
        val perWorker = mutableMapOf<String, Int>()
        for (r in results) perWorker.merge(r.substringAfter("by "), 1, Int::plus)
        println("$workers workers: ${perWorker.toSortedMap()}")
    }
    println("20 refunds took ${(System.nanoTime() - t0) / 1_000_000} ms")
}
