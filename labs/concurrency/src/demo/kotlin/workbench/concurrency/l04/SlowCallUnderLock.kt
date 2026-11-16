package workbench.concurrency.l04

import kotlin.concurrent.thread

// Eight threads make transfers. Each one first asks a fraud-check service, which takes 40 ms. Where should the lock go?
private val transferLock = Any()
private var movedCents = 0L                          // guarded by transferLock

fun main() {
    println("fraud check inside the lock:  %,5d ms".format(run(checkInsideLock = true)))
    println("fraud check outside the lock: %,5d ms".format(run(checkInsideLock = false)))
}

private fun run(checkInsideLock: Boolean): Long {
    movedCents = 0
    val t0 = System.nanoTime()
    val threads = List(8) {
        thread {
            repeat(5) {
                if (checkInsideLock) {
                    synchronized(transferLock) {
                        val ok = checkForFraud()     // 40 ms while every other thread waits
                        if (ok) movedCents += 1_999
                    }
                } else {
                    val ok = checkForFraud()         // slow work with no lock held
                    synchronized(transferLock) {     // lock only the shared update
                        if (ok) movedCents += 1_999
                    }
                }
            }
        }
    }
    threads.forEach { it.join() }
    check(movedCents == 40L * 1_999) { "lost an update: $movedCents" }
    return (System.nanoTime() - t0) / 1_000_000
}

// Stands in for a call to a fraud-check web service: 40 ms, and the answer is "looks fine".
private fun checkForFraud(): Boolean {
    Thread.sleep(40)
    return true
}
