package workbench.functional.l05.demo

data class Item(val name: String, val grams: Int)

private val basket = listOf(Item("flour", 500), Item("sugar", 200), Item("butter", 250))

fun main() {
    // 1. a sequence is a recipe: every terminal operation runs the whole chain again
    val weights = basket.asSequence().map { println("  weigh ${it.name}"); it.grams }
    println("sum = ${weights.sum()}")
    println("count = ${weights.count()}")

    // 2. some sequences can be read only once
    val once = basket.iterator().asSequence()
    println("first read: ${once.map { it.name }.toList()}")
    try {
        once.toList()
    } catch (e: IllegalStateException) {
        println("second read: ${e::class.simpleName}: ${e.message}")
    }
}
