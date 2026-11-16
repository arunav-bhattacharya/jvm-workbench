package workbench.concurrency.l12

import java.util.concurrent.ArrayBlockingQueue
import kotlin.concurrent.thread

// Closing time in the kitchen: two waiters (producers), three cooks (consumers), one bounded rail,
// shut down with poison pills. Run with -Pargs=onepill to send a single pill instead of one per cook.
private val PILL = String(charArrayOf('P', 'I', 'L', 'L'))      // a fresh object: compared by identity

fun main(args: Array<String>) {
    val onePill = args.firstOrNull() == "onepill"
    val queue = ArrayBlockingQueue<String>(4)
    val cooks = List(3) { c ->
        thread(isDaemon = true, name = "cook-$c") {
            var done = 0
            while (true) {
                val r = queue.take()
                if (r === PILL) break                          // this cook stops; the others keep going
                done++
            }
            println("${Thread.currentThread().name} got its pill after $done orders")
        }
    }
    val waiters = List(2) { me ->
        thread(name = "waiter-$me") { repeat(1_000) { i -> queue.put("order-$me-$i") } }
    }
    waiters.forEach { it.join() }                              // 1. every waiter is done...
    repeat(if (onePill) 1 else cooks.size) { queue.put(PILL) }   // 2. ...then one pill each
    cooks.forEach { it.join(1_000) }
    val stuck = cooks.count { it.isAlive }
    println("cooks still waiting: $stuck" + if (stuck > 0) " (${cooks.last { it.isAlive }.state} in take)" else "")
}
