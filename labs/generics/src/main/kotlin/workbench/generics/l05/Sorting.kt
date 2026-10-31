package workbench.generics.l05

/**
 * Returns the item that [comparator] ranks highest. Throws IllegalArgumentException when [items] is empty.
 *
 * Look at the parameter: `Comparator<in T>`. It accepts a comparator of T or of any SUPERtype of T,
 * so one Comparator<PaymentEvent> can rank a list of CardAuthorized. Write it with a loop and
 * comparator.compare; do not call maxWith from the standard library.
 */
fun <T> highest(items: List<T>, comparator: Comparator<in T>): T =
    TODO("keep the best item seen so far, using comparator.compare(a, b) > 0")

/** Ranks events by payment id, alphabetically. Used by the tests on lists of several event types. */
val byPaymentId: Comparator<PaymentEvent> = compareBy { it.paymentId }
