package workbench.concurrency.l01

import kotlin.concurrent.thread

// main returns at once. Does the program end?
fun main() {
    thread(name = "settlement-worker") {             // thread {} starts it straight away
        for (i in 1..5) {
            println("worker: settling batch $i")
            try {
                Thread.sleep(300)
            } catch (e: InterruptedException) {
                return@thread
            }
        }
        println("worker: all batches settled")
    }
    println("main: returning from main()")
}
