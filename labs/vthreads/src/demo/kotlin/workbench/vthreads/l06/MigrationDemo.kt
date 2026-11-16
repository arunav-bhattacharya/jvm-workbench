package workbench.vthreads.l06

import java.util.concurrent.Callable
import java.util.concurrent.ExecutionException
import java.util.concurrent.ExecutorService
import java.util.concurrent.Executors
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger

/**
 * 300 quote requests arrive at once. Each borrows a connection from a 10-connection pool for a
 * 5 ms query (the pool gives up after 30 ms of waiting), then makes a 100 ms call to the
 * exchange-rate service.
 * The same handler runs three ways: the old fixed pool, a plain swap to virtual threads,
 * and virtual threads with a Semaphore in front of the database.
 */
private const val REQUESTS = 300
private const val CONNECTIONS = 10

private val pool = Semaphore(CONNECTIONS)                       // the fake connection pool
private val ratesInFlight = AtomicInteger()
private val ratesPeak = AtomicInteger()

private fun query(): String {
    check(pool.tryAcquire(30, TimeUnit.MILLISECONDS)) { "connection pool: no connection after 30 ms" }
    try {
        Thread.sleep(5)                                         // the query
        return "standard"
    } finally {
        pool.release()
    }
}

private fun rateCall(): String {
    ratesPeak.accumulateAndGet(ratesInFlight.incrementAndGet()) { a, b -> maxOf(a, b) }
    try {
        Thread.sleep(100)                                       // the call to the exchange-rate service
        return "1.0842"
    } finally {
        ratesInFlight.decrementAndGet()
    }
}

private fun run(label: String, executor: ExecutorService, handler: () -> String) {
    ratesPeak.set(0)
    var ok = 0
    var failed = 0
    val t0 = System.nanoTime()
    executor.use {
        val futures = List(REQUESTS) { executor.submit(Callable { handler() }) }
        for (f in futures) {
            try {
                f.get()
                ok++
            } catch (e: ExecutionException) {
                failed++
            }
        }
    }
    println("%-34s %,6d ms   ok %3d   failed %3d   rate calls in flight at peak %3d"
        .format(label, (System.nanoTime() - t0) / 1_000_000, ok, failed, ratesPeak.get()))
}

fun main() {
    // A: today: 10 platform threads, sized to the pool
    run("A: fixed pool of 10", Executors.newFixedThreadPool(10)) { query() + rateCall() }

    // B: the one-line migration: nothing limits the database any more
    run("B: virtual threads", Executors.newVirtualThreadPerTaskExecutor()) { query() + rateCall() }

    // C: virtual threads, and the limit made explicit around the database call only
    val dbPermits = Semaphore(CONNECTIONS, true)
    run("C: virtual threads + Semaphore(10)", Executors.newVirtualThreadPerTaskExecutor()) {
        dbPermits.acquire()
        val tier = try {
            query()
        } finally {
            dbPermits.release()
        }
        tier + rateCall()
    }
}
