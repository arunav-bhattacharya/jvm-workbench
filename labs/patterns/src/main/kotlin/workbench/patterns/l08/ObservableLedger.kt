package workbench.patterns.l08

import kotlinx.coroutines.flow.SharedFlow
import kotlinx.coroutines.flow.StateFlow

/** What the ledger tells its observers: [amountMinor] was posted to [account]. Two equal postings are two events. */
data class Posted(val account: String, val amountMinor: Long)

/**
 * A ledger that other parts of the service can observe in two ways: a hand-rolled listener list
 * ([subscribe]), called directly by [post], and two coroutine flows ([events] and [balance]).
 */
class ObservableLedger {

    /**
     * Every posting, in order, to every collector that is collecting at the time. Two equal postings in
     * a row must arrive as two events. Back it with a private mutable flow and expose it read-only.
     */
    val events: SharedFlow<Posted>
        get() = TODO("a private MutableSharedFlow, exposed with asSharedFlow()")

    /** The running total of all postings, starting at 0. Its collectors only need the latest value. */
    val balance: StateFlow<Long>
        get() = TODO("a private MutableStateFlow(0L), exposed with asStateFlow()")

    /**
     * Registers [listener]. Closing the returned handle unsubscribes it. Listeners are called in
     * subscription order, and a listener may close its own handle while it is being called.
     */
    fun subscribe(listener: (Posted) -> Unit): AutoCloseable =
        TODO("add to a list that is safe to change while you iterate it; return a handle that removes it")

    /**
     * Posts one entry: add it to [balance], call every listener (one that throws must neither stop the
     * others nor make post fail), then emit it on [events].
     */
    suspend fun post(account: String, amountMinor: Long) {
        TODO("update the balance, notify the listeners safely, emit the event")
    }
}
