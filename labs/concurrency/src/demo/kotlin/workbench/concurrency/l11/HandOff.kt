package workbench.concurrency.l11

import java.util.concurrent.ArrayBlockingQueue
import kotlin.concurrent.thread

// A waiter writes tickets of 100 numbered dishes and hands each one to a cook through the rail,
// a queue. Run with -Pargs=reuse to rub out and reuse one ticket instead of handing over a new one.
fun main(args: Array<String>) {
    val reuse = args.firstOrNull() == "reuse"
    val queue = ArrayBlockingQueue<MutableList<Int>>(4)
    val tickets = 5_000
    var damaged = 0

    val cook = thread(name = "cook") {
        repeat(tickets) {
            val ticket = queue.take()                                 // the cook owns this list now
            try {
                val entries = ticket.toTypedArray()
                val ok = entries.size == 100 && entries.indices.all { i -> entries[i] == entries[0] + i }
                if (!ok) damaged++
            } catch (e: RuntimeException) {
                damaged++                                             // a list changing under you can throw, too
            }
        }
    }

    val shared = ArrayList<Int>()
    for (b in 0 until tickets) {
        val ticket = if (reuse) shared else ArrayList(100)
        ticket.clear()                                                // with reuse: rubs out a ticket the cook may be reading
        for (i in 0 until 100) ticket.add(b * 100 + i)
        queue.put(ticket)                                             // hand it over, and never touch it again
    }
    cook.join()
    println("%s: %,d tickets handed over, %,d damaged".format(if (reuse) "one ticket, reused" else "new ticket each time", tickets, damaged))
}
