package workbench.concurrency.l06

import kotlin.concurrent.thread

// The same opposite transfers, with every thread taking the locks in one global order.
private class Acct(val id: Int, var balance: Long)

fun main() {
    val a = Acct(1, 1_000_000)
    val b = Acct(2, 1_000_000)
    val t0 = System.nanoTime()
    val t1 = thread(name = "A-to-B") { repeat(100_000) { move(a, b, 1) } }
    val t2 = thread(name = "B-to-A") { repeat(100_000) { move(b, a, 1) } }
    t1.join()
    t2.join()
    println("200,000 opposite transfers in %d ms, total still %,d"
        .format((System.nanoTime() - t0) / 1_000_000, a.balance + b.balance))
}

private fun move(from: Acct, to: Acct, cents: Long) {
    val first = if (from.id < to.id) from else to    // lower id first, whatever the direction
    val second = if (first === from) to else from
    synchronized(first) {
        synchronized(second) {
            from.balance -= cents
            to.balance += cents
        }
    }
}
