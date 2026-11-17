package workbench.coroutines.l01

// The bakery's ordering library. It is callback-based, like many older libraries, and you cannot change it.
// This file is the same in src/main and src/solution.

/** What we ask the bakery for. */
data class BreadOrder(val bread: String, val loaves: Int)

/** The bakery's answer when the bread is ready: a ticket to collect it with. */
data class Pickup(val ticket: String, val loaves: Int)

/** The bakery said no. */
class SoldOutException(val reason: String) : Exception("sold out: $reason")

/** Exactly one of these is called, later, on one of the library's own threads. */
interface OrderCallback {
    fun onReady(pickup: Pickup)
    fun onFailed(error: Throwable)
}

/** A handle to an order the bakery is working on. */
fun interface PendingOrder {
    /** Asks the bakery to drop the order. A late reply may still arrive after this. */
    fun cancel()
}

interface BakeryClient {
    /** Places an order and returns at once. The answer comes later, through [callback]. */
    fun order(order: BreadOrder, callback: OrderCallback): PendingOrder
}
