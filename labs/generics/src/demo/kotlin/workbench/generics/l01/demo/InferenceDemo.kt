package workbench.generics.l01.demo

/**
 * Make the compiler tell you what it inferred. Each probe assigns a value to an Int,
 * which is wrong on purpose. The error message prints the real, inferred type.
 * Uncomment ONE probe at a time, run, read the message, comment it out again.
 */
fun main() {
    val weights = listOf(180, 150, 210)
    val mixed = listOf(180, 2.5)
    val tags = listOf("ripe", null)
    val prices = mapOf("apple" to 40, "mango" to 250L)
    val varieties = buildList { add("Gala"); add("Fuji") }
    val none = emptyList<String>()

    // val probe1: Int = weights
    // val probe2: Int = mixed
    // val probe3: Int = tags
    // val probe4: Int = prices
    // val probe5: Int = varieties
    // val probe6 = emptyList()

    println("compiled: ${weights.size + mixed.size + tags.size + prices.size + varieties.size + none.size} values")
}
