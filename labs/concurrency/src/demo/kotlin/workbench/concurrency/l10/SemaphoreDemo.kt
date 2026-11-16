package workbench.concurrency.l10

import java.util.concurrent.Semaphore
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

// 20 card checks, 5 permits, a slow web service that takes 120 ms per call. Then the bug that adds permits out of thin air.
private inline fun <T> Semaphore.withPermit(block: () -> T): T {
    acquire()                                                          // before the try
    try {
        return block()
    } finally {
        release()
    }
}

fun main() {
    val bank = Semaphore(5)                                            // the bank's service allows 5 calls at once
    val inFlight = AtomicInteger()
    val peak = AtomicInteger()
    val t0 = System.nanoTime()
    val requests = List(20) {
        thread {
            bank.withPermit {
                peak.accumulateAndGet(inFlight.incrementAndGet(), Math::max)
                Thread.sleep(120)                                      // the call to the slow web service
                inFlight.decrementAndGet()
            }
        }
    }
    requests.forEach { it.join() }
    println("20 calls, peak in flight ${peak.get()}, took ${(System.nanoTime() - t0) / 1_000_000} ms")

    // permits belong to nobody: any thread can release, even one that never acquired
    val carPark = Semaphore(5)
    carPark.release()
    println("new Semaphore(5), then one stray release(): ${carPark.availablePermits()} permits")
}
