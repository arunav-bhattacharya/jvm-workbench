package workbench.generics.l05

/**
 * The bell by the back door. Whoever wants to know about deliveries listens; when an item of type E
 * arrives, the bell calls every listener with it.
 *
 * Listeners are plain functions `(E) -> Unit`. A function type is contravariant in its parameter
 * (`Function1<in P, out R>`), so a listener written for ANY Fruit can listen to a DeliveryBell<Apple>.
 * You get that for free; your job is the storage and the ringing.
 */
class DeliveryBell<E> {

    /** Adds [listener]. Listeners are called in the order they started listening. */
    fun listen(listener: (E) -> Unit) {
        TODO("remember the listener")
    }

    /** Calls every listener with [item] and returns how many listeners were called. */
    fun ring(item: E): Int = TODO("call each listener in order")
}
