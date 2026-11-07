package workbench.events.l02.demo.dispatch

import workbench.events.l02.demo.MoneyMovement
import workbench.events.l02.demo.PaymentCaptured
import workbench.events.l02.demo.PaymentDeclined
import workbench.events.l02.demo.PaymentEvent
import kotlin.reflect.KClass
import kotlin.reflect.cast

// The event model (PaymentEvent and friends) is in DemoModel.kt, one package up.

/** Keys every handler by the class it was subscribed under; delivery can look up keys two ways. */
class Bus(private val walkSupertypes: Boolean) {
    private val handlers = HashMap<KClass<*>, MutableList<(PaymentEvent) -> Unit>>()

    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: (E) -> Unit) {
        handlers.getOrPut(type) { mutableListOf() }.add { event -> handler(type.cast(event)) }
    }

    fun publish(event: PaymentEvent) {
        val keys = if (walkSupertypes) dispatchKeys(event.javaClass) else listOf(event::class)
        for (key in keys) handlers[key]?.forEach { it(event) }
    }
}

/** The event's class, then its supertypes that are events, nearest first. */
fun dispatchKeys(type: Class<*>): List<KClass<*>> {
    val found = LinkedHashSet<Class<*>>()
    val queue = ArrayDeque(listOf(type))
    while (queue.isNotEmpty()) {
        val c = queue.removeFirst()
        if (!PaymentEvent::class.java.isAssignableFrom(c) || !found.add(c)) continue
        queue.addAll(c.interfaces)
        c.superclass?.let(queue::add)
    }
    return found.map { it.kotlin }
}

fun main() {
    for (walk in listOf(false, true)) {
        val ran = mutableListOf<String>()
        val bus = Bus(walk)
        bus.subscribe(PaymentEvent::class) { ran += "audit" }
        bus.subscribe(MoneyMovement::class) { ran += "movements" }
        bus.subscribe(PaymentCaptured::class) { ran += "ledger" }
        bus.publish(PaymentCaptured("pay_7781", 1_999))
        println("%-22s %s".format(if (walk) "walking supertypes:" else "exact class only:", ran))
    }
    println("keys for PaymentCaptured: " + dispatchKeys(PaymentCaptured::class.java).map { it.simpleName })
    println("keys for PaymentDeclined: " + dispatchKeys(PaymentDeclined::class.java).map { it.simpleName })
}
