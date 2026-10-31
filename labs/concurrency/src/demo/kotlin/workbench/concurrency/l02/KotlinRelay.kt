package workbench.concurrency.l02

import kotlin.concurrent.thread

// A polling loop that follows the interruption protocol, in Kotlin.
fun main() {
    val relay = thread(name = "outbox-relay") {
        val me = Thread.currentThread()
        while (!me.isInterrupted) {                // property syntax for isInterrupted()
            // poll the outbox and publish here
            try {
                Thread.sleep(50)                   // no try/catch is forced on you in Kotlin...
            } catch (e: InterruptedException) {
                me.interrupt()                     // ...but the protocol is the same: restore the flag
            }
        }
        println("relay stopped, flag = ${me.isInterrupted}")
    }
    Thread.sleep(300)
    relay.interrupt()
    relay.join()
    println("relay alive after join: ${relay.isAlive}")
}
