package workbench.jmm.l03

import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.LongAdder
import kotlin.concurrent.thread

private var plain = 0
@Volatile private var vol = 0
private val atomic = AtomicInteger()
private val adder = LongAdder()

private const val THREADS = 4
private const val PER_THREAD = 1_000_000

/** Four threads each add 1,000,000 to four kinds of counter. Which ones add up? */
fun main() {
    hammer("plain Int") { plain++ }
    hammer("@Volatile Int") { vol++ }
    hammer("AtomicInteger") { atomic.incrementAndGet() }
    hammer("LongAdder") { adder.increment() }
    println("expected %,d each".format(THREADS * PER_THREAD))
    println("plain %,d   @Volatile %,d   atomic %,d   adder %,d".format(plain, vol, atomic.get(), adder.sum()))
}

private fun hammer(name: String, increment: () -> Unit) {
    val ts = List(THREADS) { t ->
        thread(name = "$name-$t") { repeat(PER_THREAD) { increment() } }
    }
    ts.forEach { it.join() }   // join: the final reads in main see every thread's writes
}
