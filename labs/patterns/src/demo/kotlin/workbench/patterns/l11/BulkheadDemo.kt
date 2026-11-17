package workbench.patterns.l11

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.sync.Semaphore
import java.util.concurrent.atomic.AtomicInteger

// 200 coroutines book a courier whose booking line takes at most 20 calls at once: wait for a free line, or fail fast.

suspend fun runBulkhead(mode: String, failFast: Boolean) {
    val permits = Semaphore(20)
    val onLine = AtomicInteger()
    val mostOnLine = AtomicInteger()
    val done = AtomicInteger()
    val rejected = AtomicInteger()
    val start = System.nanoTime()
    coroutineScope {                                                    // waits for all 200 children
        repeat(200) {
            launch {
                if (failFast) {
                    if (!permits.tryAcquire()) { rejected.incrementAndGet(); return@launch }   // bulkhead: busy tone, at once
                } else {
                    permits.acquire()                                                         // limiter: wait on hold
                }
                try {
                    mostOnLine.accumulateAndGet(onLine.incrementAndGet(), ::maxOf)
                    delay(20)                                                                 // a booking takes 20 ms
                    onLine.decrementAndGet()
                    done.incrementAndGet()
                } finally {
                    permits.release()
                }
            }
        }
    }
    val ms = (System.nanoTime() - start) / 1_000_000
    println("%-10s done %3d, rejected %3d, most at once %2d, about %d ms".format(mode, done.get(), rejected.get(), mostOnLine.get(), ms))
}

fun main() = runBlocking {
    runBulkhead("wait", failFast = false)
    runBulkhead("fail fast", failFast = true)
}
