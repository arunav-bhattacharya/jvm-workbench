package workbench.concurrency.l07

import java.util.concurrent.locks.StampedLock
import kotlin.concurrent.thread

// A writer keeps moving an FX quote; the ask is always bid + 2. A reader reads both fields
// optimistically for one second and counts how often validate() caught a half-written quote.
private class Quote {
    val lock = StampedLock()
    var bid = 100L                                    // guarded by lock; ask == bid + 2 when no write is in progress
    var ask = 102L
}

@Volatile
private var done = false

fun main() {
    val q = Quote()
    val writer = thread {
        var v = 100L
        while (!done) {
            val stamp = q.lock.writeLock()
            try {
                q.bid = ++v
                repeat(20) { Thread.onSpinWait() }    // widens the half-written moment
                q.ask = v + 2
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
        var b = q.bid; var a = q.ask                  // 2. copy the fields into locals
        val torn = a - b != 2L
        if (q.lock.validate(stamp)) {                 // 3. did a writer get in since step 1?
            if (torn) tornPassed++                    //    never happens
        } else {
            failed++
            if (torn) tornCaught++
            stamp = q.lock.readLock()                 // 4. fall back to a real read lock
            try { b = q.bid; a = q.ask } finally { q.lock.unlockRead(stamp) }
        }
    }
    done = true
    writer.join()
    println("reads: %,d   failed validate(): %,d   torn quotes caught: %,d   torn quotes that passed validate(): %d"
        .format(reads, failed, tornCaught, tornPassed))
}
