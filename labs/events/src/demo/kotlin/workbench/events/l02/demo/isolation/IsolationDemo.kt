package workbench.events.l02.demo.isolation

import workbench.events.l02.demo.PaymentCaptured
import workbench.events.l02.demo.PaymentEvent
import java.util.concurrent.CopyOnWriteArrayList

// The event model (PaymentEvent and friends) is in DemoModel.kt, one package up.

/** A list of handlers, stored in [handlers]; publish can isolate failures or not. */
class Bus(private val handlers: MutableList<(PaymentEvent) -> Unit>, private val isolate: Boolean) {
    fun subscribe(handler: (PaymentEvent) -> Unit): AutoCloseable {
        handlers += handler
        return AutoCloseable { handlers -= handler }
    }

    fun publish(event: PaymentEvent) {
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
    once = bus.subscribe { println("  welcome email, once"); once?.close() }   // unsubscribes itself
    bus.subscribe { throw IllegalStateException("ledger is down") }
    bus.subscribe { println("  receipt for ${it.paymentId}") }
    try {
        bus.publish(PaymentCaptured("pay_7781", 1_999))
        bus.publish(PaymentCaptured("pay_7782", 250))
    } catch (e: Exception) {
        println("  publish threw $e")
    }
}

fun main() {
    scenario("ArrayList, no isolation:", Bus(ArrayList(), isolate = false))
    scenario("CopyOnWriteArrayList, no isolation:", Bus(CopyOnWriteArrayList(), isolate = false))
    scenario("CopyOnWriteArrayList, isolated:", Bus(CopyOnWriteArrayList(), isolate = true))
}
