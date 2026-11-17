package workbench.coroutines.l09

import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** The cook puts 5 plates through the hatch as fast as she can; the helper needs 100 ms per plate. */
suspend fun run(label: String, hatch: Channel<Int>) = coroutineScope {
    val t0 = System.nanoTime()
    fun ms() = (System.nanoTime() - t0) / 1_000_000
    val sendTimes = mutableListOf<Long>()
    launch {
        for (plate in 1..5) { hatch.send(plate); sendTimes += ms() }
        hatch.close() // no more plates: the helper's for loop ends after the last one
    }
    val received = mutableListOf<Int>()
    for (plate in hatch) { delay(100); received += plate }
    println("%-12s send() returned at %-26s received %s".format(label, sendTimes.toString() + " ms", received))
}

fun main() = runBlocking {
    run("RENDEZVOUS", Channel(Channel.RENDEZVOUS))
    run("capacity 2", Channel(2))
    run("UNLIMITED", Channel(Channel.UNLIMITED))
    run("CONFLATED", Channel(Channel.CONFLATED))
}
