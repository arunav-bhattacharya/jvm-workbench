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
    val helpers = args.firstOrNull()?.toInt() ?: 4
    val t0 = System.nanoTime()
    coroutineScope {
        // 1. one cook puts 20 dishes through the hatch, one at a time
        val hatch = produce { for (i in 1..20) send("dish-$i") }
        // 2. fan-out: each dish goes to exactly one helper
        val table = Channel<String>()
        val team = List(helpers) { h ->
            launch {
                for (dish in hatch) {
                    delay(Random.nextLong(50, 150)) // carrying it, serving it
                    table.send("$dish by helper $h")
                }
            }
        }
        // 3. fan-in: close the table channel when every helper is done
        launch { team.joinAll(); table.close() }
        val perHelper = mutableMapOf<String, Int>()
        for (served in table) perHelper.merge(served.substringAfter("by "), 1, Int::plus)
        println("$helpers helpers: ${perHelper.toSortedMap()}")
    }
    println("20 dishes took ${(System.nanoTime() - t0) / 1_000_000} ms")
}
