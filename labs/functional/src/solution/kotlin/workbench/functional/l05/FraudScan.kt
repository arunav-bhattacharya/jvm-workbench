package workbench.functional.l05

/** One card payment in the day's feed. Amounts are in cents; [country] is the card's issuing country. */
data class Payment(val id: Long, val merchant: String, val amountCents: Long, val country: String)

fun firstSuspicious(feed: List<Payment>, riskScore: (Payment) -> Int): Payment? =
    feed.asSequence()                          // one payment at a time through the whole chain
        .map { it to riskScore(it) }
        .filter { (_, score) -> score >= 90 }
        .map { (payment, _) -> payment }
        .firstOrNull()                         // stops pulling after the first match
// feed.firstOrNull { riskScore(it) >= 90 } is just as good: one inlined loop that also stops early.

fun firstSuspiciousForeign(feed: List<Payment>, riskScore: (Payment) -> Int, n: Int): List<Long> =
    feed.asSequence()
        .filter { it.country != "NL" }         // the cheap check first, so domestic cards never reach the model
        .filter { riskScore(it) >= 90 }
        .map { it.id }
        .take(n)                               // after n ids, nothing upstream is pulled again
        .toList()
