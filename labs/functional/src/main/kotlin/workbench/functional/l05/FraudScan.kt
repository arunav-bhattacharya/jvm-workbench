package workbench.functional.l05

/** One card payment in the day's feed. Amounts are in cents; [country] is the card's issuing country. */
data class Payment(val id: Long, val merchant: String, val amountCents: Long, val country: String)

/**
 * Returns the first payment in [feed] whose risk score is 90 or more, or null if there is none.
 *
 * [riskScore] stands for a call to the fraud model: about 2 ms each, and billed per call. Score only as
 * many payments as you need. If the first suspicious payment is the 4,217th in the feed, [riskScore]
 * must run exactly 4,217 times.
 *
 * This version gives the right answer, but it scores the whole feed before it looks for a match.
 * Fix it without changing the signature.
 */
fun firstSuspicious(feed: List<Payment>, riskScore: (Payment) -> Int): Payment? =
    feed.map { it to riskScore(it) }
        .filter { (_, score) -> score >= 90 }
        .map { (payment, _) -> payment }
        .firstOrNull()

/**
 * Returns the ids of the first [n] payments that are foreign (issued outside "NL") and score 90 or more,
 * in feed order. Fewer than [n] if the feed runs out.
 *
 * The model is only licensed for foreign cards: never pass a domestic ("NL") payment to [riskScore].
 * And stop as soon as you have [n] ids: [riskScore] must not run on any payment after the nth match.
 */
fun firstSuspiciousForeign(feed: List<Payment>, riskScore: (Payment) -> Int, n: Int): List<Long> =
    TODO("filter, then score, then take(n), one payment at a time")
