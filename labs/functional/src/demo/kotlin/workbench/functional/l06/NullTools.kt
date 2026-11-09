package workbench.functional.l06

data class CardOnFile(val token: String?, val country: String)

data class RefundLine(val paymentId: String, val amountMinor: Long?, val reason: String?)

class Checkout {
    var pendingRefund: Long? = null

    fun process(send: (Long) -> Unit) {
        // Uncomment the next line and run: a var property is never smart-cast, even right after the check.
        // if (pendingRefund != null) send(pendingRefund)
        pendingRefund?.let(send)        // reads the property once, then works with that value
    }
}

fun tokenFor(card: CardOnFile?): String {
    val token = card?.token ?: return "declined: no card token"   // ?. chains, ?: can return
    return "charge with ${token.take(4)}..."
}

fun main() {
    println(tokenFor(CardOnFile("tok_4242424242", "NL")))
    println(tokenFor(CardOnFile(null, "NL")))
    println(tokenFor(null))

    // takeIf: a filter for one value; the result is nullable
    val amount = 1_999L
    println("takeIf positive: ${amount.takeIf { it > 0 }}, takeIf over 5,000: ${amount.takeIf { it > 5_000 }}")

    // requireNotNull and checkNotNull: a message, the right exception, and a smart cast afterwards
    val line = RefundLine("p9", null, "duplicate")
    try {
        val cents = requireNotNull(line.amountMinor) { "refund ${line.paymentId} has no amount" }
        println(cents)
    } catch (e: IllegalArgumentException) {
        println("requireNotNull: ${e::class.simpleName}: ${e.message}")
    }
    val ledgerSession: String? = null
    try {
        checkNotNull(ledgerSession) { "ledger session not opened" }
    } catch (e: IllegalStateException) {
        println("checkNotNull:   ${e::class.simpleName}: ${e.message}")
    }

    // mapNotNull: transform and drop the nulls in one step
    val lines = listOf(line, RefundLine("p10", 500, null), RefundLine("p11", 1_200, "fraud"))
    println("reasons: ${lines.mapNotNull { it.reason }}")

    val checkout = Checkout().apply { pendingRefund = 700 }
    checkout.process { println("sending refund of $it") }
}
