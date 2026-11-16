package workbench.concurrency.l07

import java.util.concurrent.locks.StampedLock
import kotlin.concurrent.thread

// The bank's two prices for the euro: it buys at one price and sells 2 cents higher.
// A writer keeps moving both prices. A reader reads them optimistically for one second
// and counts how often validate() caught a half-written pair.
private class EuroPrices {
    val lock = StampedLock()
    var buy = 100L                                    // guarded by lock; sell == buy + 2 when no write is in progress
    var sell = 102L
}

@Volatile
private var done = false

fun main() {
    val q = EuroPrices()
    val writer = thread {
        var v = 100L
        while (!done) {
            val stamp = q.lock.writeLock()
            try {
                q.buy = ++v
                repeat(20) { Thread.onSpinWait() }    // widens the half-written moment
                q.sell = v + 2
            } finally {
                q.lock.unlockWrite(stamp)
            }
        }
    }

    var reads = 0L; var failed = 0L; var tornCaught = 0L; var tornPassed = 0L
    val end = System.nanoTime() + 1_000_000_000L
    while (System.nanoTime() < end) {
        reads++
        var stamp = q.lock.tryOptimisticRead()        // 1. no lock taken, just a version number
        var b = q.buy; var s = q.sell                 // 2. copy the fields into locals
        val torn = s - b != 2L
        if (q.lock.validate(stamp)) {                 // 3. did a writer get in since step 1?
            if (torn) tornPassed++                    //    never happens
        } else {
            failed++
            if (torn) tornCaught++
            stamp = q.lock.readLock()                 // 4. fall back to a real read lock
            try { b = q.buy; s = q.sell } finally { q.lock.unlockRead(stamp) }
        }
    }
    done = true
    writer.join()
    println("reads: %,d   failed validate(): %,d   torn pairs caught: %,d   torn pairs that passed validate(): %d"
        .format(reads, failed, tornCaught, tornPassed))
}
