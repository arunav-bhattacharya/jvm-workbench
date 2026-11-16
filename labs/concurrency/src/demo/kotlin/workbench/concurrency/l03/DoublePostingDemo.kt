package workbench.concurrency.l03

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// A replay hands the same 1,000 payment events to eight consumer threads. Each consumer posts a
// payment to the ledger only if no one has posted it yet: check-then-act on a ConcurrentHashMap.
fun main() {
    val postedBy = ConcurrentHashMap<Int, String>()          // payment id -> the consumer that posted it
    val postings = AtomicInteger()
    val consumers = List(8) { c ->
        thread(start = false, name = "consumer-$c") {
            for (payment in 0 until 1_000) {
                if (!postedBy.containsKey(payment)) {        // check
                    repeat(300) { Thread.onSpinWait() }      // a slow step: the fraud check
                    postedBy[payment] = "consumer-$c"        // act
                    postings.incrementAndGet()               // the money moves
                }
            }
        }
    }
    consumers.forEach { it.start() }
    consumers.forEach { it.join() }
    println("payments: 1,000  postings: %,d  duplicate postings: %,d".format(postings.get(), postings.get() - 1_000))
}
