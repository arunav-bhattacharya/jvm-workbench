package workbench.generics.l05.demo

/** One comparator, written for the supertype, sorts lists of any subtype. */
val byPaymentId: Comparator<PaymentEvent> = compareBy { it.paymentId }

fun main() {
    val auths = listOf(CardAuthorized("pay_3", 1_200), CardAuthorized("pay_1", 350))
    val refunds = listOf(RefundIssued("pay_9", 50), RefundIssued("pay_4", 75))

    // sortedWith takes a Comparator<in T>: a comparator of T or of any supertype of T
    println(auths.sortedWith(byPaymentId).map { it.paymentId })
    println(refunds.sortedWith(byPaymentId).map { it.paymentId })

    val forCards: Comparator<in CardAuthorized> = byPaymentId     // fine with a use-site `in`

    // Wrong move. Uncomment, predict the error, then run.
    // val strict: Comparator<CardAuthorized> = byPaymentId
    println("forCards compares: ${forCards.compare(auths[0], auths[1])}")
}
