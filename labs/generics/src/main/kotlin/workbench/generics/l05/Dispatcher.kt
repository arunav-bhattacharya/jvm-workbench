package workbench.generics.l05

/**
 * Delivers events of type E to every subscribed handler.
 *
 * Handlers are plain functions `(E) -> Unit`. A function type is contravariant in its parameter
 * (`Function1<in P, out R>`), so a handler written for ANY PaymentEvent can subscribe to a
 * Dispatcher<CardAuthorized>. You get that for free; your job is the storage and the delivery.
 */
class Dispatcher<E> {

    /** Adds [handler]. Handlers are called in the order they subscribed. */
    fun subscribe(handler: (E) -> Unit) {
        TODO("remember the handler")
    }

    /** Calls every handler with [event] and returns how many handlers were called. */
    fun publish(event: E): Int = TODO("call each handler in order")
}
