package workbench.patterns.l07

// Three strategies for one decision: which PSP does the router try first?

data class PspQuote(val psp: String, val feeMinor: Long, val p95Millis: Long)

fun main() {
    val quotes = listOf(
        PspQuote("Northpay", 30, 200),
        PspQuote("Adyx", 25, 900),
        PspQuote("Kestrel", 30, 120),
    )

    // each value is a complete strategy: no class per algorithm
    val policies: Map<String, Comparator<PspQuote>> = mapOf(
        "cheapest" to compareBy<PspQuote> { it.feeMinor },
        "fastest" to compareBy<PspQuote> { it.p95Millis },
        "cheapest, then fastest" to compareBy<PspQuote> { it.feeMinor }.thenBy { it.p95Millis },
    )

    // sortedWith is the context: it owns the algorithm and asks the strategy one question
    policies.forEach { (name, order) -> println("$name: ${quotes.sortedWith(order).map { it.psp }}") }
}
