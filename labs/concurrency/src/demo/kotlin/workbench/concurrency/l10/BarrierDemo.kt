package workbench.concurrency.l10

import java.util.concurrent.BrokenBarrierException
import java.util.concurrent.CyclicBarrier
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import kotlin.concurrent.thread

// Three threads add up the shop's three tills, day by day, and meet at one barrier that resets itself.
// Then a day when one till never reports.
fun main() {
    val sales = LongArray(3)                                      // one slot per till, written by its own thread
    var day = 0
    val endOfDay = CyclicBarrier(3) {                             // runs once per day, before anyone moves on
        println("  day %d closed by %s: sales %,d".format(++day, Thread.currentThread().name, sales.sum()))
    }

    val tills = List(3) { me ->
        thread(name = "till-$me") {
            try {
                for (d in 1..3) {
                    Thread.sleep(50L * (me + 1))                      // the tills finish at different times
                    sales[me] = 1_000L * d * (me + 1)
                    endOfDay.await()                                  // wait for the other two
                }
                // day 4: till 2 never reports, the others give up after 300 ms
                if (me != 2) endOfDay.await(300, TimeUnit.MILLISECONDS)
            } catch (e: TimeoutException) {
                println("  ${Thread.currentThread().name}: TimeoutException, barrier now broken")
            } catch (e: BrokenBarrierException) {
                println("  ${Thread.currentThread().name}: BrokenBarrierException")
            }
        }
    }
    tills.forEach { it.join() }
    println("broken: ${endOfDay.isBroken}")
}
