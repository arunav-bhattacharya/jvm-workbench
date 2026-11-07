package workbench.coroutines.l09

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** A producer sends 5 batch ids as fast as it can; the consumer needs 100 ms per id. */
suspend fun run(label: String, channel: Channel<Int>) = coroutineScope {
    val t0 = System.nanoTime()
    fun ms() = (System.nanoTime() - t0) / 1_000_000
    val sendTimes = mutableListOf<Long>()
    launch {
        for (id in 1..5) { channel.send(id); sendTimes += ms() }
        channel.close() // no more ids: the consumer's for loop ends after the last one
    }
    val received = mutableListOf<Int>()
    for (id in channel) { delay(100); received += id }
    println("%-12s send() returned at %-26s received %s".format(label, sendTimes.toString() + " ms", received))
}

fun main() = runBlocking {
    run("RENDEZVOUS", Channel(Channel.RENDEZVOUS))
    run("capacity 2", Channel(2))
    run("UNLIMITED", Channel(Channel.UNLIMITED))
    run("CONFLATED", Channel(Channel.CONFLATED))
}
