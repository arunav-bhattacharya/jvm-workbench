package workbench.concurrency.l07

import java.util.concurrent.TimeUnit
import java.util.concurrent.locks.ReentrantLock
import kotlin.concurrent.thread
import kotlin.concurrent.withLock

// A batch holds the ledger lock for 1.5 s. Three threads want in, each in a different way.
private val ledger = ReentrantLock()
private val monitor = Any()

fun main() {
    val batch = thread(name = "batch") {
        ledger.withLock {
            synchronized(monitor) {               // the batch holds the lock AND a monitor
                try { Thread.sleep(1_500) } catch (e: InterruptedException) { Thread.currentThread().interrupt() }
            }
        }
    }
    Thread.sleep(100)                             // let the batch get in first

    val api = thread(start = false, name = "api") {
        val t0 = System.nanoTime()
        if (ledger.tryLock(200, TimeUnit.MILLISECONDS)) {          // wait at most 200 ms
            try { println("api: got the lock") } finally { ledger.unlock() }
        } else {
            println("api: gave up after %d ms and answered 503".format((System.nanoTime() - t0) / 1_000_000))
        }
    }

    val report = thread(start = false, name = "report") {
        try {
            ledger.lockInterruptibly()                             // an interrupt can cancel this wait
            try { println("report: got the lock") } finally { ledger.unlock() }
        } catch (e: InterruptedException) {
            println("report: interrupted while waiting, gave up cleanly")
        }
    }

    val legacy = thread(start = false, name = "legacy") {
        synchronized(monitor) {                                    // no way to give up here
            println("legacy: got the monitor at last, interrupted=${Thread.currentThread().isInterrupted}")
        }
    }

    api.start()
    report.start()
    legacy.start()
    Thread.sleep(400)
    println("states: report=${report.state}, legacy=${legacy.state}")
    report.interrupt()
    legacy.interrupt()
    listOf(api, report, legacy, batch).forEach { it.join() }
}
