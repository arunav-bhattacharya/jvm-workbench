package workbench.patterns.l07

// Three strategies for one decision: which courier does the shop ask first?

data class CourierQuote(val courier: String, val priceCents: Long, val minutes: Long)

fun main() {
    val quotes = listOf(
        CourierQuote("Pedal Post", 450, 30),
        CourierQuote("Big Blue Vans", 350, 90),
        CourierQuote("Kestrel", 450, 20),
    )

    // each value is a complete strategy: no class per algorithm
    val policies: Map<String, Comparator<CourierQuote>> = mapOf(
        "cheapest" to compareBy<CourierQuote> { it.priceCents },
        "fastest" to compareBy<CourierQuote> { it.minutes },
        "cheapest, then fastest" to compareBy<CourierQuote> { it.priceCents }.thenBy { it.minutes },
    )

    // sortedWith is the context: it owns the algorithm and asks the strategy one question
    policies.forEach { (name, order) -> println("$name: ${quotes.sortedWith(order).map { it.courier }}") }
}
