package workbench.concurrency.l02

import java.time.Duration
import kotlin.concurrent.thread

// join(timeout) gives up waiting; join() waits for the end and makes the result visible.
private var priceCents = 0L                        // plain field: join() is what makes the write visible

fun main() {
    val fetch = thread(name = "price-fetch") {
        try {
            Thread.sleep(500)                      // stands in for a slow web service that answers in 500 ms
        } catch (e: InterruptedException) {
            Thread.currentThread().interrupt()
        }
        priceCents = 10_842
    }

    val ended = fetch.join(Duration.ofMillis(100)) // JDK 19+: returns whether it ended
    println("after join(100 ms): ended=$ended, alive=${fetch.isAlive}, price=$priceCents")

    fetch.join()                                   // no timeout: wait for the end
    println("after join():       alive=${fetch.isAlive}, price=$priceCents")
}
