package workbench.concurrency.l03

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// The same 1,000 payments reach eight teller threads, as if every payment arrived eight times.
// Each teller records a payment only if nobody has recorded it yet: check-then-act on a ConcurrentHashMap.
fun main() {
    val recordedBy = ConcurrentHashMap<Int, String>()        // payment id -> the teller that recorded it
    val recorded = AtomicInteger()
    val tellers = List(8) { c ->
        thread(start = false, name = "teller-$c") {
            for (payment in 0 until 1_000) {
                if (!recordedBy.containsKey(payment)) {      // check
                    repeat(300) { Thread.onSpinWait() }      // a slow step: is the payment genuine?
                    recordedBy[payment] = "teller-$c"        // act
                    recorded.incrementAndGet()               // the money moves
                }
            }
        }
    }
    tellers.forEach { it.start() }
    tellers.forEach { it.join() }
    println("payments: 1,000  times recorded: %,d  duplicates: %,d".format(recorded.get(), recorded.get() - 1_000))
}
