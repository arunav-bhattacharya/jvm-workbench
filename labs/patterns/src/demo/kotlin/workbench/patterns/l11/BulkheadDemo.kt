package workbench.patterns.l11

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Semaphore
import java.util.concurrent.atomic.AtomicInteger

// 200 coroutines call a PSP that should see at most 20 at once: wait for a permit, or fail fast.

suspend fun runBulkhead(mode: String, failFast: Boolean) {
    val permits = Semaphore(20)
    val inFlight = AtomicInteger()
    val mostInFlight = AtomicInteger()
    val done = AtomicInteger()
    val rejected = AtomicInteger()
    val start = System.nanoTime()
    coroutineScope {                                                    // waits for all 200 children
        repeat(200) {
            launch {
                if (failFast) {
                    if (!permits.tryAcquire()) { rejected.incrementAndGet(); return@launch }   // bulkhead: reject now
                } else {
                    permits.acquire()                                                         // limiter: wait in line
                }
                try {
                    mostInFlight.accumulateAndGet(inFlight.incrementAndGet(), ::maxOf)
                    delay(20)                                                                 // the PSP takes 20 ms
                    inFlight.decrementAndGet()
                    done.incrementAndGet()
                } finally {
                    permits.release()
                }
            }
        }
    }
    val ms = (System.nanoTime() - start) / 1_000_000
    println("%-10s done %3d, rejected %3d, most in flight %2d, about %d ms".format(mode, done.get(), rejected.get(), mostInFlight.get(), ms))
}

fun main() = runBlocking {
    runBulkhead("wait", failFast = false)
    runBulkhead("fail fast", failFast = true)
}
