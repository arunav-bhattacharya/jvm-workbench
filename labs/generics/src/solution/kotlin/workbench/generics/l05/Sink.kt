package workbench.generics.l05

// in T: a Sink only takes T values in, so a Sink<PaymentEvent> can safely act as a Sink<CardAuthorized>
interface Sink<in T> {
    fun accept(item: T)
}

// the class has to be invariant: `items` hands T back out, `accept` takes T in
class CollectingSink<T> : Sink<T> {
    private val accepted = ArrayList<T>()

    val items: List<T>
        get() = accepted.toList()   // a copy, so callers can't change our history

    override fun accept(item: T) {
        accepted.add(item)
    }
}

fun feedAll(events: List<PaymentEvent>, sink: Sink<PaymentEvent>): Int {
    for (e in events) sink.accept(e)
    return events.size
}
