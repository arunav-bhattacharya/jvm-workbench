package workbench.events.l02.demo.isolation

import workbench.events.l02.demo.ParcelCollected
import workbench.events.l02.demo.ParcelEvent
import java.util.concurrent.CopyOnWriteArrayList

// The event model (ParcelEvent and friends) is in DemoModel.kt, one package up.

/** A list of handlers, stored in [handlers]; publish can isolate failures or not. */
class Bus(private val handlers: MutableList<(ParcelEvent) -> Unit>, private val isolate: Boolean) {
    fun subscribe(handler: (ParcelEvent) -> Unit): AutoCloseable {
        handlers += handler
        return AutoCloseable { handlers -= handler }
    }

    fun publish(event: ParcelEvent) {
        for (h in handlers) {
            if (!isolate) { h(event); continue }
            try {
                h(event)
            } catch (e: Exception) {
                println("  (error handler: ${e.message})")
            }
        }
    }
}

fun scenario(title: String, bus: Bus) {
    println(title)
    var once: AutoCloseable? = null
    once = bus.subscribe { println("  welcome text, once"); once?.close() }   // unsubscribes itself
    bus.subscribe { throw IllegalStateException("load board is down") }
    bus.subscribe { println("  text to sender: ${it.parcelId} is on its way") }
    try {
        bus.publish(ParcelCollected("PP-7781", 2_500))
        bus.publish(ParcelCollected("PP-7782", 1_200))
    } catch (e: Exception) {
        println("  publish threw $e")
    }
}

fun main() {
    scenario("ArrayList, no isolation:", Bus(ArrayList(), isolate = false))
    scenario("CopyOnWriteArrayList, no isolation:", Bus(CopyOnWriteArrayList(), isolate = false))
    scenario("CopyOnWriteArrayList, isolated:", Bus(CopyOnWriteArrayList(), isolate = true))
}
