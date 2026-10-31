package workbench.generics.l05

/**
 * Something that accepts items: an audit log, a Kafka producer, a metrics counter. It is a consumer.
 *
 * TODO 1: make Sink contravariant, so a Sink<PaymentEvent> can be used where a Sink<CardAuthorized>
 * is expected. Add `in` to the type parameter.
 */
interface Sink<T> {
    fun accept(item: T)
}

/**
 * A Sink that remembers everything it accepted, in order. The class itself stays invariant:
 * it hands its items back out through [items], so its own T is both in and out.
 */
class CollectingSink<T> : Sink<T> {
    /** Everything accepted so far, oldest first. */
    val items: List<T>
        get() = TODO("return a read-only view or copy of what was accepted")

    override fun accept(item: T) {
        TODO("remember the item")
    }
}

/** Sends every event to [sink], in order, and returns how many were sent. */
fun feedAll(events: List<PaymentEvent>, sink: Sink<PaymentEvent>): Int =
    TODO("call sink.accept for each event")
