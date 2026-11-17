package workbench.functional.l06.demo

data class Guest(val name: String, val favorite: String?)

data class ShoppingLine(val item: String, val grams: Int?, val note: String?)

class Scale {
    var lastReading: Int? = null

    fun report(show: (Int) -> Unit) {
        // Uncomment the next line and run: a var property is never smart-cast, even right after the check.
        // if (lastReading != null) show(lastReading)
        lastReading?.let(show)          // reads the property once, then works with that value
    }
}

fun starterFor(guest: Guest?): String {
    val favorite = guest?.favorite ?: return "no favorite known: serve soup"   // ?. chains, ?: can return
    return "start with ${favorite.lowercase()}"
}

fun main() {
    println(starterFor(Guest("Ana", "Tomato salad")))
    println(starterFor(Guest("Ben", null)))
    println(starterFor(null))

    // takeIf: a filter for one value; the result is nullable
    val grams = 250
    println("takeIf positive: ${grams.takeIf { it > 0 }}, takeIf over 1,000: ${grams.takeIf { it > 1_000 }}")

    // requireNotNull and checkNotNull: a message, the right exception, and a smart cast afterwards
    val line = ShoppingLine("flour", null, "the strong kind")
    try {
        val g = requireNotNull(line.grams) { "shopping line ${line.item} has no amount" }
        println(g)
    } catch (e: IllegalArgumentException) {
        println("requireNotNull: ${e::class.simpleName}: ${e.message}")
    }
    val scaleUnit: String? = null
    try {
        checkNotNull(scaleUnit) { "scale not switched on" }
    } catch (e: IllegalStateException) {
        println("checkNotNull:   ${e::class.simpleName}: ${e.message}")
    }

    // mapNotNull: transform and drop the nulls in one step
    val lines = listOf(line, ShoppingLine("sugar", 200, null), ShoppingLine("eggs", null, "free range"))
    println("notes: ${lines.mapNotNull { it.note }}")

    val scale = Scale().apply { lastReading = 450 }
    scale.report { println("the scale says $it g") }
}
