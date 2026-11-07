package workbench.generics.l06.demo

interface PaymentEvent { val paymentId: String }
data class CardAuthorized(override val paymentId: String, val cents: Long) : PaymentEvent
data class RefundIssued(override val paymentId: String, val cents: Long) : PaymentEvent

/** Reads AND writes T, so it can't be declared out or in. It stays invariant. */
class Ledger<T> {
    private val entries = mutableListOf<T>()
    fun record(entry: T) { entries += entry }
    fun latest(): T = entries.last()
}

// Only reads: ask for a read view. A Ledger<CardAuthorized> fits.
fun latestId(ledger: Ledger<out PaymentEvent>): String = ledger.latest().paymentId

// Only writes cards: ask for a write view. A Ledger<PaymentEvent> fits.
fun recordCard(ledger: Ledger<in CardAuthorized>, id: String, cents: Long) = ledger.record(CardAuthorized(id, cents))

fun main() {
    val cards = Ledger<CardAuthorized>()
    val everything = Ledger<PaymentEvent>()
    everything.record(RefundIssued("pay_1", 500))

    recordCard(cards, "pay_2", 1_200)
    recordCard(everything, "pay_3", 350)
    println("${latestId(cards)} ${latestId(everything)}")

    // Wrong move: the class is invariant, so the plain type still doesn't fit.
    // val strict: Ledger<PaymentEvent> = cards
}

// Predict each line, then uncomment it alone and run.
// fun redundant(events: List<out PaymentEvent>) {}         // 1
// fun conflicting(events: List<in PaymentEvent>) {}        // 2
// fun <out T> onFunction(t: T) {}                          // 3
