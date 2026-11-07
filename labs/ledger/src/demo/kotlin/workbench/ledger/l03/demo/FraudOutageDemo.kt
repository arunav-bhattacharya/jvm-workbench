package workbench.ledger.l03.demo

import java.util.concurrent.Callable
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.ExecutionException
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.ThreadLocalRandom
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import java.util.concurrent.atomic.LongAdder

private const val BUDGET_NANOS = 300_000_000L        // every request answers within 300 ms
private const val STAND_IN_CENTS = 5_000L            // stand-in limit: up to 50.00 goes through unchecked
private val permits = Semaphore(20)                  // the fraud bulkhead
private val inFlight = AtomicInteger()
private val mostInFlight = AtomicInteger()
private val verdicts = ConcurrentHashMap<String, LongAdder>()
private val slowestMs = AtomicLong()

// the fraud call, on its own virtual thread: a permit first, then the remote call
private fun fraudCall(latencyMs: Long, deadline: Long): Boolean {
    if (!permits.tryAcquire(deadline - System.nanoTime(), TimeUnit.NANOSECONDS)) throw TimeoutException("no permit")
    try {
        mostInFlight.accumulateAndGet(inFlight.incrementAndGet(), ::maxOf)
        try {
            Thread.sleep(latencyMs)                  // the fraud service; an interrupt ends it early
        } finally {
            inFlight.decrementAndGet()
        }
        return true
    } finally {
        permits.release()
    }
}

private fun screen(cents: Long, latencyMs: Long): String {
    val deadline = System.nanoTime() + BUDGET_NANOS
    Executors.newVirtualThreadPerTaskExecutor().use { perCall ->
        val call = perCall.submit(Callable { fraudCall(latencyMs, deadline) })
        return try {
            if (call.get(deadline - System.nanoTime(), TimeUnit.NANOSECONDS)) "approved" else "declined"
        } catch (e: TimeoutException) {              // our deadline passed first
            call.cancel(true)                        // interrupt the call: it holds a permit
            fallback(cents)
        } catch (e: ExecutionException) {            // no permit before the deadline
            fallback(cents)
        }
    }
}

private fun fallback(cents: Long) = if (cents <= STAND_IN_CENTS) "stand-in" else "timed out"

/** 400 requests a second for 3 seconds, each on its own virtual thread. Pass "outage" to slow the fraud service to 2 s. */
fun main(args: Array<String>) {
    val latencyMs = if (args.firstOrNull() == "outage") 2_000L else 20L
    Executors.newVirtualThreadPerTaskExecutor().use { perRequest ->
        repeat(300) {                                // 300 rounds of 4 requests, 10 ms apart
            repeat(4) {
                val cents = 1 + ThreadLocalRandom.current().nextLong(20_000)
                perRequest.execute {
                    val t0 = System.nanoTime()
                    verdicts.computeIfAbsent(screen(cents, latencyMs)) { LongAdder() }.increment()
                    slowestMs.accumulateAndGet((System.nanoTime() - t0) / 1_000_000, ::maxOf)
                }
            }
            Thread.sleep(10)
        }
    }
    println("fraud service takes $latencyMs ms: ${verdicts.toSortedMap()}")
    println("most fraud calls in flight: ${mostInFlight.get()}, slowest reply: ${slowestMs.get()} ms")
}
