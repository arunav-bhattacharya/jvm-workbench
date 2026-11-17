package workbench.patterns.l11

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration.Companion.seconds

// The packing rail: the counter sends order slips, four packers take them, and close() sends every packer home.

fun main() = runBlocking {
    val orders = 1_000
    val rail = Channel<Int>(capacity = 16)                          // bounded: send suspends when the rail is full
    val packed = AtomicInteger()

    val packers = List(4) {
        launch(Dispatchers.Default) {
            for (slip in rail) packed.incrementAndGet()             // ends when the rail is closed and empty
        }
    }

    repeat(orders) { rail.send(it) }
    rail.close()                                                    // one call sends every packer home

    val finished = withTimeoutOrNull(2.seconds) { packers.joinAll() } != null
    println("packed $packed of $orders, all packers finished: $finished")
    if (!finished) {
        packers.forEach { it.cancel() }
        println("the packers were still waiting at the rail: nobody closed it")
    }
}
