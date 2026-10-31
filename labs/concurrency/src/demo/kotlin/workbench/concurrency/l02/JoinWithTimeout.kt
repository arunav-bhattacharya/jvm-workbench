package workbench.concurrency.l02

import java.time.Duration
import kotlin.concurrent.thread

// join(timeout) gives up waiting; join() waits for the end and makes the result visible.
private var rateCents = 0L                         // plain field: join() is what makes the write visible

fun main() {
    val fetch = thread(name = "fx-fetch") {
        try {
            Thread.sleep(500)                      // stands in for a 500 ms call to an FX-rate service
        } catch (e: InterruptedException) {
            Thread.currentThread().interrupt()
        }
        rateCents = 10_842
    }

    val ended = fetch.join(Duration.ofMillis(100)) // JDK 19+: returns whether it ended
    println("after join(100 ms): ended=$ended, alive=${fetch.isAlive}, rate=$rateCents")

    fetch.join()                                   // no timeout: wait for the end
    println("after join():       alive=${fetch.isAlive}, rate=$rateCents")
}
