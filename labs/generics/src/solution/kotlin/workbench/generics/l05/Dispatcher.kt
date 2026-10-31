package workbench.generics.l05

class Dispatcher<E> {
    private val handlers = ArrayList<(E) -> Unit>()

    fun subscribe(handler: (E) -> Unit) {
        handlers.add(handler)   // a (PaymentEvent) -> Unit is already a (CardAuthorized) -> Unit
    }

    fun publish(event: E): Int {
        for (h in handlers) h(event)
        return handlers.size
    }
}
