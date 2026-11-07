package workbench.concurrency.l08

import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.LongAdder
import kotlin.concurrent.thread

// updateAndGet retries your function when it loses a race. Count how often the function really runs.
fun main() {
    val balance = AtomicLong()
    val calls = LongAdder()
    val go = CountDownLatch(1)
    val ts = List(4) {
        thread {
            go.await()
            repeat(250_000) {
                balance.updateAndGet { b ->
                    calls.increment()           // a side effect: imagine this sent a notification
                    b + 1
                }
            }
        }
    }
    go.countDown()                              // all four start together
    ts.forEach { it.join() }
    println("updates: %,d   times the function ran: %,d".format(balance.get(), calls.sum()))
}
