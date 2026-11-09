package workbench.functional.l05

fun interface SettlementApi {
    fun page(number: Int): List<Payment>
}

fun allSettlements(api: SettlementApi): Sequence<Payment> = sequence {
    var number = 0
    while (true) {
        val page = api.page(number++)          // runs only when the consumer wants the next payment
        if (page.isEmpty()) break              // an empty page ends the sequence
        yieldAll(page)                         // suspends here between payments
    }
}
