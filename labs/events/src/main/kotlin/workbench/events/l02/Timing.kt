package workbench.events.l02

import java.util.concurrent.ConcurrentHashMap

/** A source of nanoseconds. Tests pass a fake one, so no timing test depends on the real clock. */
fun interface Ticker {
    fun nanos(): Long

    companion object {
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
 * under [name].
 *
 * TODO 7: read timings.ticker before and after calling the wrapped handler, and record the difference
 * even when the handler throws. The exception must still reach the bus.
 */
fun <E : PaymentEvent> Handler<E>.timed(name: String, timings: Timings): Handler<E> =
    TODO("wrap this handler: same interface, plus timing")
