package workbench.functional.l05

data class Refund(val id: Int, val amountCents: Long)

private val refunds = listOf(Refund(1, 500), Refund(2, 1_200), Refund(3, 300))

fun main() {
    // 1. a sequence is a recipe: every terminal operation runs the whole chain again
    val amounts = refunds.asSequence().map { println("  map ${it.id}"); it.amountCents }
    println("sum = ${amounts.sum()}")
    println("count = ${amounts.count()}")

    // 2. some sequences can be read only once
    val once = refunds.iterator().asSequence()
    println("first read: ${once.map { it.id }.toList()}")
    try {
        once.toList()
    } catch (e: IllegalStateException) {
        println("second read: ${e::class.simpleName}: ${e.message}")
    }
}
