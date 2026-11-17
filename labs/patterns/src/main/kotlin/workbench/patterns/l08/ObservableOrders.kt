package workbench.patterns.l08

import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow

/** What the shop tells its observers: [customer] ordered [quantity] of [item]. Two equal orders are two events. */
data class Ordered(val customer: String, val item: String, val quantity: Int)

/**
 * The shop's orders, which other parts of the program can observe in two ways: a hand-rolled listener
 * list ([subscribe]), called directly by [place], and two coroutine flows ([events] and [itemsToday]).
 */
class ObservableOrders {

    /**
     * Every order, in turn, to every collector that is collecting at the time. Two equal orders in a row
     * must arrive as two events. Back it with a private mutable flow and expose it read-only.
     */
    val events: SharedFlow<Ordered>
        get() = TODO("a private MutableSharedFlow, exposed with asSharedFlow()")

    /** How many items were ordered today in all, starting at 0. Its collectors only need the latest value. */
    val itemsToday: StateFlow<Int>
        get() = TODO("a private MutableStateFlow(0), exposed with asStateFlow()")

    /**
     * Registers [listener]. Closing the returned handle unsubscribes it. Listeners are called in
     * subscription order, and a listener may close its own handle while it is being called.
     */
    fun subscribe(listener: (Ordered) -> Unit): AutoCloseable =
        TODO("add to a list that is safe to change while you iterate it; return a handle that removes it")

    /**
     * Places one order: add its quantity to [itemsToday], call every listener (one that throws must
     * neither stop the others nor make place fail), then emit it on [events].
     */
    suspend fun place(customer: String, item: String, quantity: Int) {
        TODO("update the count, tell the listeners safely, emit the event")
    }
}
