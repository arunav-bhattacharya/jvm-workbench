package workbench.concurrency.l12

import java.util.concurrent.ArrayBlockingQueue
import kotlin.concurrent.thread

// Two producers, three consumers, one bounded queue, shut down with poison pills.
// Run with -Pargs=onepill to send a single pill instead of one per consumer.
private val PILL = String(charArrayOf('P', 'I', 'L', 'L'))      // a fresh object: compared by identity

fun main(args: Array<String>) {
    val onePill = args.firstOrNull() == "onepill"
    val queue = ArrayBlockingQueue<String>(4)
    val consumers = List(3) { c ->
        thread(isDaemon = true, name = "consumer-$c") {
            var done = 0
            while (true) {
                val r = queue.take()
                if (r === PILL) break                          // this consumer stops; the others keep going
                done++
            }
            println("${Thread.currentThread().name} got its pill after $done records")
        }
    }
    val producers = List(2) { me ->
        thread { repeat(1_000) { i -> queue.put("settle-$me-$i") } }
    }
    producers.forEach { it.join() }                            // 1. every producer is done...
    repeat(if (onePill) 1 else consumers.size) { queue.put(PILL) }   // 2. ...then one pill each
    consumers.forEach { it.join(1_000) }
    val stuck = consumers.count { it.isAlive }
    println("consumers still waiting: $stuck" + if (stuck > 0) " (${consumers.last { it.isAlive }.state} in take)" else "")
}
