package workbench.concurrency.l03

import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

/** Eight buyers race for the same 1,000 seats using check-then-act on a ConcurrentHashMap. */
fun main() {
    val owners = ConcurrentHashMap<Int, String>()
    val sold = AtomicInteger()
    val buyers = (0 until 8).map { b ->
        thread(start = false) {
            for (seat in 0 until 1_000) {
                if (!owners.containsKey(seat)) {               // check
                    repeat(300) { Thread.onSpinWait() }        // a slow step
                    owners[seat] = "buyer-$b"                  // act
                    sold.incrementAndGet()
                }
            }
        }
    }
    buyers.forEach { it.start() }
    buyers.forEach { it.join() }
    println("seats: 1,000  tickets sold: %,d  double-booked: %,d".format(sold.get(), sold.get() - 1_000))
}
