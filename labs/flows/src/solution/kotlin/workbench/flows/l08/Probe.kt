package workbench.flows.l08

import java.util.concurrent.CopyOnWriteArrayList

/** One reading from the wireless oven probe, for example reading 42 at 63 °C. */
data class ProbeReading(val seq: Int, val celsius: Int)

/** What the probe's library calls back. It may call it on any of its own threads. */
interface ProbeListener {
    fun onReading(reading: ProbeReading)
    fun onError(error: Throwable)
    fun onClosed()
}

/** Returned by [FakeProbe.register]. Call [unregister] to stop the callbacks. */
fun interface Registration {
    fun unregister()
}

/**
 * A made-up probe library that tests drive by hand. Register and unregister are thread-safe,
 * and every callback runs on the thread that calls [fire], [fail], [close] or [burst].
 */
class FakeProbe {
    private val listeners = CopyOnWriteArrayList<ProbeListener>()

    val listenerCount: Int get() = listeners.size

    fun register(listener: ProbeListener): Registration {
        listeners += listener
        return Registration { listeners -= listener }
    }

    fun fire(reading: ProbeReading) = listeners.forEach { it.onReading(reading) }
    fun fail(error: Throwable) = listeners.forEach { it.onError(error) }
    fun close() = listeners.forEach { it.onClosed() }

    /** On connect the real probe replays the readings it stored while nobody listened, in one synchronous burst, like this. */
    fun burst(count: Int) = repeat(count) { fire(ProbeReading(it, 60)) }
}
