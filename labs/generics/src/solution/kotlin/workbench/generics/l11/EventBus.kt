package workbench.generics.l11

import kotlin.reflect.KClass
import kotlin.reflect.safeCast

class EventBus {
    private val handlers = HashMap<KClass<out PaymentEvent>, MutableList<(PaymentEvent) -> Unit>>()

    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: (E) -> Unit) {
        // the adapter takes any PaymentEvent and passes it on only if it really is an E
        handlers.getOrPut(type) { mutableListOf() }.add { event -> type.safeCast(event)?.let(handler) }
    }

    // noinline: the lambda is stored in the map, so it must stay a real object
    inline fun <reified E : PaymentEvent> subscribe(noinline handler: (E) -> Unit) = subscribe(E::class, handler)

    fun publish(event: PaymentEvent): Int {
        val list = handlers[event::class] ?: return 0
        for (h in list) h(event)
        return list.size
    }
}
