package workbench.vthreads.l06

import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.LongAdder
import java.util.concurrent.locks.LockSupport

/**
 * Requests arrive at a steady rate, one virtual thread each. A request waits for one of 10
 * database permits, runs a 20 ms query, then makes a 100 ms FX call. A sampler prints two
 * gauges you would put on a dashboard, and the summary checks Little's law:
 * requests in flight = throughput x time in the system.
 *
 * Args: requests per second (default 400), seconds (default 2).
 */
private val dbPermits = Semaphore(10, true)
private val inFlight = AtomicInteger()
private val done = LongAdder()
private val nanosInSystem = LongAdder()

@Volatile
private var stop = false

private fun handle() {
    val start = System.nanoTime()
    inFlight.incrementAndGet()
    try {
        dbPermits.acquire()
        try {
            Thread.sleep(20)                                    // the database query
        } finally {
            dbPermits.release()
        }
        Thread.sleep(100)                                       // the FX call
    } catch (e: InterruptedException) {
        Thread.currentThread().interrupt()
    } finally {
        inFlight.decrementAndGet()
        nanosInSystem.add(System.nanoTime() - start)
        done.increment()
    }
}

fun main(args: Array<String>) {
    val rate = args.getOrNull(0)?.toInt() ?: 400
    val seconds = args.getOrNull(1)?.toInt() ?: 2
    val gapNanos = 1_000_000_000L / rate
    val t0 = System.nanoTime()

    // sample every 10 ms for the average; print every 250 ms
    var totalInFlight = 0L
    var samples = 0L
    val sampler = Thread.ofPlatform().daemon().start {
        while (!stop) {
            LockSupport.parkNanos(10_000_000)
            totalInFlight += inFlight.get()
            samples++
            if (samples % 25 == 0L) {
                println("t=%,5d ms   in flight %4d   waiting for a db permit %4d"
                    .format((System.nanoTime() - t0) / 1_000_000, inFlight.get(), dbPermits.queueLength))
            }
        }
    }

    Executors.newVirtualThreadPerTaskExecutor().use { perRequest ->
        for (i in 0 until rate * seconds) {
            val due = t0 + i * gapNanos
            while (true) {                                      // steady arrivals
                val wait = due - System.nanoTime()
                if (wait <= 0) break
                LockSupport.parkNanos(wait)
            }
            perRequest.execute { handle() }
        }
    }                                                           // waits for the last requests
    val elapsed = (System.nanoTime() - t0) / 1e9
    stop = true
    sampler.join()

    val throughput = done.sum() / elapsed                      // requests per second
    val timeInSystem = nanosInSystem.sum() / 1e9 / done.sum()
    println("throughput %.0f/s, mean time in system %.0f ms".format(throughput, timeInSystem * 1000))
    println("Little's law: throughput x time = %.1f; measured average in flight = %.1f"
        .format(throughput * timeInSystem, totalInFlight.toDouble() / samples))
}
