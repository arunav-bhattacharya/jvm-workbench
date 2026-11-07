package workbench.concurrency.l11

import java.util.concurrent.ArrayBlockingQueue
import kotlin.concurrent.thread

// A request thread fills batches of 100 ledger entries and hands each one to a writer thread
// through a queue. Run with -Pargs=reuse to reuse one list instead of handing over a new one.
fun main(args: Array<String>) {
    val reuse = args.firstOrNull() == "reuse"
    val queue = ArrayBlockingQueue<MutableList<Int>>(4)
    val batches = 5_000
    var damaged = 0

    val writer = thread(name = "ledger-writer") {
        repeat(batches) {
            val batch = queue.take()                                  // the writer owns this list now
            try {
                val entries = batch.toTypedArray()
                val ok = entries.size == 100 && entries.indices.all { i -> entries[i] == entries[0] + i }
                if (!ok) damaged++
            } catch (e: RuntimeException) {
                damaged++                                             // a list changing under you can throw, too
            }
        }
    }

    val shared = ArrayList<Int>()
    for (b in 0 until batches) {
        val batch = if (reuse) shared else ArrayList(100)
        batch.clear()                                                 // with reuse: clears a list the writer may be reading
        for (i in 0 until 100) batch.add(b * 100 + i)
        queue.put(batch)                                              // hand it over, and never touch it again
    }
    writer.join()
    println("%s: %,d batches handed over, %,d damaged".format(if (reuse) "reused list" else "new list each time", batches, damaged))
}
