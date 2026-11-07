package workbench.generics.l11

import kotlin.reflect.KClass

/**
 * Routes each published event to the handlers subscribed to its exact class.
 * Events flow OUT of publishers (producers); handlers take them IN (consumers).
 */
class EventBus {
    // keys come from event::class, which is a KClass<out PaymentEvent>
    private val handlers = HashMap<KClass<out PaymentEvent>, MutableList<(PaymentEvent) -> Unit>>()

    /**
     * Subscribes [handler] to events of class [type].
     *
     * TODO 4: you can't add an (E) -> Unit to a list of (PaymentEvent) -> Unit: a function that only
     * takes CardAuthorized can't be handed a RefundIssued. Store an adapter instead: a
     * (PaymentEvent) -> Unit that calls handler only when type.safeCast(event) is not null.
     */
    fun <E : PaymentEvent> subscribe(type: KClass<E>, handler: (E) -> Unit) {
        TODO("getOrPut the list for type, add an adapter lambda")
    }

    /**
     * TODO 5: the Kotlin-friendly version, `bus.subscribe<CardAuthorized> { ... }`. Make it inline with a
     * reified E and delegate with E::class. The handler is stored, not called, so mark it `noinline`.
     */
    fun <E : PaymentEvent> subscribe(handler: (E) -> Unit) {
        TODO("inline + reified E + noinline handler, then subscribe(E::class, handler)")
    }

    /** TODO 6: calls every handler for event::class, in subscription order, and returns how many ran. */
    fun publish(event: PaymentEvent): Int = TODO("look up event::class, call each handler")
}
