package workbench.ledger.l03.demo

import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.withLock

private val merchantMonitor = Any()                  // a hot merchant account, guarded by a monitor...
private val merchantLock = ReentrantLock()           // ...or by a ReentrantLock
private var merchantBalance = 0L

private fun journalWrite() = Thread.sleep(20)        // 20 ms of blocking I/O

/**
 * One carrier thread. 20 virtual threads pay a hot merchant account while a ticker tries to tick
 * every 10 ms. Where the journal write sits decides whether the carrier stays free.
 */
fun main() {
    System.setProperty("jdk.virtualThreadScheduler.parallelism", "1")   // before the first virtual thread
    println("JDK ${Runtime.version()}, 1 carrier thread")
    runVariant("journal inside synchronized   ") { synchronized(merchantMonitor) { journalWrite(); merchantBalance += 100 } }
    runVariant("journal inside ReentrantLock  ") { merchantLock.withLock { journalWrite(); merchantBalance += 100 } }
    runVariant("journal first, then the lock  ") { journalWrite(); merchantLock.withLock { merchantBalance += 100 } }
}

private fun runVariant(label: String, transfer: () -> Unit) {
    var longestGap = 0L
    val ticker = Thread.ofVirtual().start {
        var last = System.nanoTime()
        repeat(40) {
            Thread.sleep(10)
            val now = System.nanoTime()
            longestGap = maxOf(longestGap, (now - last) / 1_000_000)
            last = now
        }
    }
    Thread.sleep(5)
    val t0 = System.nanoTime()
    val payers = List(20) { Thread.ofVirtual().start(transfer) }
    payers.forEach { it.join() }
    val ms = (System.nanoTime() - t0) / 1_000_000
    ticker.join()
    println("$label 20 transfers in %4d ms, longest gap between ticks: %3d ms".format(ms, longestGap))
}
