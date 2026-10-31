package workbench.generics.l01.demo

/**
 * Make the compiler tell you what it inferred. Each probe assigns a value to an Int,
 * which is wrong on purpose. The error message prints the real, inferred type.
 * Uncomment ONE probe at a time, run, read the message, comment it out again.
 */
fun main() {
    val amounts = listOf(1200, 350, 99)
    val mixed = listOf(1, 2.5)
    val tags = listOf("card", null)
    val fees = mapOf("EUR" to 100, "USD" to 250L)
    val keys = buildList { add("idem_1"); add("idem_2") }
    val none = emptyList<String>()

    // val probe1: Int = amounts
    // val probe2: Int = mixed
    // val probe3: Int = tags
    // val probe4: Int = fees
    // val probe5: Int = keys
    // val probe6 = emptyList()

    println("compiled: ${amounts.size + mixed.size + tags.size + fees.size + keys.size + none.size} values")
}
