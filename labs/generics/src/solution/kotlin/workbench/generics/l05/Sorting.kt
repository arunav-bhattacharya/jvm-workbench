package workbench.generics.l05

fun <T> highest(items: List<T>, comparator: Comparator<in T>): T {
    require(items.isNotEmpty()) { "highest of an empty list" }
    var best = items[0]
    for (item in items) {
        // the comparator accepts T (or a supertype of T): both arguments are T, so they fit
        if (comparator.compare(item, best) > 0) best = item
    }
    return best
}

val byPaymentId: Comparator<PaymentEvent> = compareBy { it.paymentId }
