package workbench.patterns.l11

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeoutOrNull
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration.Companion.seconds

// One producer, four consumers, a bounded channel, and close() as the poison pill for all of them.

fun main() = runBlocking {
    val jobs = 1_000
    val channel = Channel<Int>(capacity = 16)                       // bounded: send suspends when full
    val processed = AtomicInteger()

    val workers = List(4) {
        launch(Dispatchers.Default) {
            for (job in channel) processed.incrementAndGet()        // ends when the channel is closed and drained
        }
    }

    repeat(jobs) { channel.send(it) }
    channel.close()                                                 // one call stops every worker

    val finished = withTimeoutOrNull(2.seconds) { workers.joinAll() } != null
    println("processed $processed of $jobs, all workers finished: $finished")
    if (!finished) {
        workers.forEach { it.cancel() }
        println("the workers were still waiting to receive: nobody closed the channel")
    }
}
