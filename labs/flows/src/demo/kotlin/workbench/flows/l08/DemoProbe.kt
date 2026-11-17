package workbench.flows.l08

import java.util.concurrent.CopyOnWriteArrayList

// A made-up wireless oven probe with a listener API, used by the demos of this lesson.
data class ProbeEvent(val seq: Int, val celsius: Int)

interface ProbeEventListener {
    fun onEvent(event: ProbeEvent)
    fun onError(error: Throwable)
    fun onClosed()
}

fun interface ProbeRegistration {
    fun unregister()
}

class DemoProbe {
    val listeners = CopyOnWriteArrayList<ProbeEventListener>()

    fun register(listener: ProbeEventListener): ProbeRegistration {
        listeners += listener
        println("    [probe] registered (listeners=${listeners.size})")
        return ProbeRegistration { listeners -= listener; println("    [probe] unregistered (listeners=${listeners.size})") }
    }

    fun fire(event: ProbeEvent) = listeners.forEach { it.onEvent(event) }
    fun fail(error: Throwable) = listeners.forEach { it.onError(error) }
    fun close() = listeners.forEach { it.onClosed() }
}
