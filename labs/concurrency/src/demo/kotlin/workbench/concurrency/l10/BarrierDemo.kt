package workbench.concurrency.l10

import java.util.concurrent.BrokenBarrierException
import java.util.concurrent.CyclicBarrier
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import kotlin.concurrent.thread

// Three workers, three rounds, one barrier that resets itself. Then a round where one worker never shows up.
fun main() {
    val shares = LongArray(3)
    val endOfDay = CyclicBarrier(3) {                             // runs once per round, before anyone moves on
        println("  day closed by %s: exposure %,d".format(Thread.currentThread().name, shares.sum()))
    }

    val workers = List(3) { me ->
        thread(name = "worker-$me") {
            try {
                for (day in 1..3) {
                    Thread.sleep(50L * (me + 1))                      // workers finish at different times
                    shares[me] = 1_000L * day * (me + 1)
                    endOfDay.await()                                  // wait for the other two
                }
                // day 4: worker 2 never arrives, the others give up after 300 ms
                if (me != 2) endOfDay.await(300, TimeUnit.MILLISECONDS)
            } catch (e: TimeoutException) {
                println("  ${Thread.currentThread().name}: TimeoutException, barrier now broken")
            } catch (e: BrokenBarrierException) {
                println("  ${Thread.currentThread().name}: BrokenBarrierException")
            }
        }
    }
    workers.forEach { it.join() }
    println("broken: ${endOfDay.isBroken}")
}
