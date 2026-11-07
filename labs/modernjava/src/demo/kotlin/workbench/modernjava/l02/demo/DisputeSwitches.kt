package workbench.modernjava.l02.demo

sealed interface Dispute {
    data class Opened(val caseId: String, val amountMinor: Long) : Dispute
    data class EvidenceSent(val caseId: String) : Dispute
    data class Won(val caseId: String) : Dispute
    data class Lost(val caseId: String, val amountMinor: Long) : Dispute

    // Step 2: uncomment this class. Kotlin has no permits clause to edit.
    // data class Arbitration(val caseId: String, val feeMinor: Long) : Dispute
}

fun label(d: Dispute): String = when (d) {                 // exhaustive, no else
    is Dispute.Opened -> "opened"
    is Dispute.EvidenceSent -> "evidence sent"
    is Dispute.Won -> "won"
    is Dispute.Lost -> "lost"
}

fun ledgerImpact(d: Dispute): Long = when (d) {            // exhaustive, no else
    is Dispute.Opened -> -d.amountMinor                     // money held back while the case runs
    is Dispute.EvidenceSent -> 0
    is Dispute.Won -> 0
    is Dispute.Lost -> -d.amountMinor
}

fun slaDays(d: Dispute): Int = when (d) {
    is Dispute.Opened -> 7
    is Dispute.EvidenceSent -> 30
    else -> 0                                               // "and anything else": the compiler stops checking
}

/** Three whens over one sealed type. Add a subtype and see which ones the compiler finds. */
fun main() {
    val all = listOf(Dispute.Opened("cb_1", 4_200), Dispute.EvidenceSent("cb_1"), Dispute.Won("cb_1"), Dispute.Lost("cb_2", 990))
    for (d in all) {
        println("%-14s impact %6d   sla %2d days".format(label(d), ledgerImpact(d), slaDays(d)))
    }
}
