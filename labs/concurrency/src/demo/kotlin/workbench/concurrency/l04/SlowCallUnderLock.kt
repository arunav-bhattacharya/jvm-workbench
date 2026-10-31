package workbench.concurrency.l04

import kotlin.concurrent.thread

// Eight threads authorize payments. Each call to the issuer takes 40 ms. Where should the lock go?
private val issuerLock = Any()
private var approvedCents = 0L                       // guarded by issuerLock

fun main() {
    println("issuer call inside the lock:  %,5d ms".format(run(callInsideLock = true)))
    println("issuer call outside the lock: %,5d ms".format(run(callInsideLock = false)))
}

private fun run(callInsideLock: Boolean): Long {
    approvedCents = 0
    val t0 = System.nanoTime()
    val threads = List(8) {
        thread {
            repeat(5) {
                if (callInsideLock) {
                    synchronized(issuerLock) {
                        val ok = callIssuer()        // 40 ms while every other thread waits
                        if (ok) approvedCents += 1_999
                    }
                } else {
                    val ok = callIssuer()            // slow work with no lock held
                    synchronized(issuerLock) {       // lock only the shared update
                        if (ok) approvedCents += 1_999
                    }
                }
            }
        }
    }
    threads.forEach { it.join() }
    check(approvedCents == 40L * 1_999) { "lost an update: $approvedCents" }
    return (System.nanoTime() - t0) / 1_000_000
}

private fun callIssuer(): Boolean {
    Thread.sleep(40)
    return true
}
