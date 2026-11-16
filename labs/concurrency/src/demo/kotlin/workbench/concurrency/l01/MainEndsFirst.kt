package workbench.concurrency.l01

import kotlin.concurrent.thread

// main returns at once. Does the program end?
fun main() {
    thread(name = "report-worker") {                 // thread {} starts it straight away
        for (i in 1..5) {
            println("worker: printing page $i of the sales report")
            try {
                Thread.sleep(300)
            } catch (e: InterruptedException) {
                return@thread
            }
        }
        println("worker: report printed")
    }
    println("main: returning from main()")
}
