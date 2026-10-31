package workbench.concurrency.l02

import kotlin.concurrent.thread

// Watch the interrupt flag: set by interrupt(), cleared when sleep() throws, restored by you.
fun main() {
    val worker = thread(name = "worker") {
        val me = Thread.currentThread()
        try {
            Thread.sleep(10_000)                   // Kotlin doesn't force this try/catch on you
        } catch (e: InterruptedException) {
            println("1. caught InterruptedException, flag is now ${me.isInterrupted}")
            me.interrupt()                         // restore it: comment this line out and run again
            println("2. after interrupt(), flag is ${me.isInterrupted}")
        }
        println("3. isInterrupted only reads it:  ${me.isInterrupted}")
        println("4. Thread.interrupted() reads AND clears: ${Thread.interrupted()}")
        println("5. so now the flag is ${me.isInterrupted}")
    }
    Thread.sleep(200)
    worker.interrupt()                             // a request, not a command
    worker.join()
}
