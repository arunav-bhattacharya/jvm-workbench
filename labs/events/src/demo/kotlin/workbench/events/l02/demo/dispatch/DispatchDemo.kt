package workbench.events.l02.demo.dispatch

import workbench.events.l02.demo.DeliveryFailed
import workbench.events.l02.demo.Handover
import workbench.events.l02.demo.ParcelCollected
import workbench.events.l02.demo.ParcelEvent
import kotlin.reflect.KClass
import kotlin.reflect.cast

// The event model (ParcelEvent and friends) is in DemoModel.kt, one package up.

/** Keys every handler by the class it was subscribed under; delivery can look up keys two ways. */
class Bus(private val walkSupertypes: Boolean) {
    private val handlers = HashMap<KClass<*>, MutableList<(ParcelEvent) -> Unit>>()

    fun <E : ParcelEvent> subscribe(type: KClass<E>, handler: (E) -> Unit) {
        handlers.getOrPut(type) { mutableListOf() }.add { event -> handler(type.cast(event)) }
    }

    fun publish(event: ParcelEvent) {
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
        if (!ParcelEvent::class.java.isAssignableFrom(c) || !found.add(c)) continue
        queue.addAll(c.interfaces)
        c.superclass?.let(queue::add)
    }
    return found.map { it.kotlin }
}

fun main() {
    for (walk in listOf(false, true)) {
        val ran = mutableListOf<String>()
        val bus = Bus(walk)
        bus.subscribe(ParcelEvent::class) { ran += "tracking" }
        bus.subscribe(Handover::class) { ran += "handovers" }
        bus.subscribe(ParcelCollected::class) { ran += "load" }
        bus.publish(ParcelCollected("PP-7781", 2_500))
        println("%-22s %s".format(if (walk) "walking supertypes:" else "exact class only:", ran))
    }
    println("keys for ParcelCollected: " + dispatchKeys(ParcelCollected::class.java).map { it.simpleName })
    println("keys for DeliveryFailed: " + dispatchKeys(DeliveryFailed::class.java).map { it.simpleName })
}
