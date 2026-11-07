// Java calls the top-level functions in this file as Handlers.timed(...), not TimingKt.timed(...)
@file:JvmName("Handlers")

package workbench.events.l03

import java.util.concurrent.ConcurrentHashMap

/** A source of nanoseconds. Tests pass a fake one, so no timing test depends on the real clock. */
fun interface Ticker {
    fun nanos(): Long

    companion object {
        @JvmField                                    // Java reads Ticker.SYSTEM
        val SYSTEM: Ticker = Ticker { System.nanoTime() }
    }
}

/** Total time and number of calls per name. Safe to use from many threads. */
class Timings(val ticker: Ticker = Ticker.SYSTEM) {
    private val nanos = ConcurrentHashMap<String, Long>()
    private val calls = ConcurrentHashMap<String, Int>()

    fun record(name: String, elapsedNanos: Long) {
        nanos.merge(name, elapsedNanos) { a, b -> a + b }
        calls.merge(name, 1) { a, b -> a + b }
    }

    fun totalNanos(name: String): Long = nanos[name] ?: 0
    fun calls(name: String): Int = calls[name] ?: 0
}

/**
 * A decorator: returns a Handler of the same type that times the one it wraps and records the time
 * under [name]. It records in `finally`, so a handler that throws is timed too, and the exception
 * still reaches the bus.
 */
fun <E : PaymentEvent> Handler<E>.timed(name: String, timings: Timings): Handler<E> {
    val inner = this
    return Handler { event ->
        val start = timings.ticker.nanos()
        try {
            inner.handle(event)
        } finally {
            timings.record(name, timings.ticker.nanos() - start)
        }
    }
}
