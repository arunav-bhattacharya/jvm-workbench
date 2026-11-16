package workbench.flows.l03

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.buffer
import kotlinx.coroutines.flow.channelFlow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.produceIn
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

var t0 = 0L
fun at(s: String) = println("  t=%3d %-46s thread=%s".format(System.currentTimeMillis() - t0, s, Thread.currentThread().name))

fun main() = runBlocking {
    println("=== flow { } with two launched producers")
    try {
        flow {
            coroutineScope {
                launch { emit("north-1") }
                launch { emit("east-1") }
            }
        }.collect { println("  got $it") }
    } catch (e: IllegalStateException) {
        println("  " + e.message!!.lines().drop(1).joinToString("\n  ").trim())
    }

    println("=== channelFlow: two acquirer feeds, one mailbox")
    t0 = System.currentTimeMillis()
    channelFlow {
        launch(Dispatchers.IO) { repeat(2) { delay(30); send("north-$it"); at("sent north-$it") } }
        launch(Dispatchers.Default) { repeat(2) { delay(45); send("east-$it"); at("sent east-$it") } }
        at("builder block returns (children still running)")
    }.collect { at("collect $it") }
    at("channelFlow completed after both children")

    println("=== produceIn: a hot channel in your scope")
    t0 = System.currentTimeMillis()
    coroutineScope {
        val mailbox = flow { at("upstream started"); for (i in 1..4) { emit(i); at("emitted $i") } }
            .buffer(1)
            .produceIn(this)
        at("produceIn returned a ReceiveChannel")
        delay(100)
        at("receiving now: ${mailbox.receive()}")
        mailbox.cancel()
        at("cancelled the channel")
    }
}
