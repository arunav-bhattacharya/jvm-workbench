package workbench.functional.l05.demo

enum class Bake { GOLDEN, RAW, BURNT }

data class Cookie(val id: String, val grams: Int, val bake: Bake)

/** One tray out of the oven: three golden cookies, one raw, one burnt. */
val tray = listOf(
    Cookie("c1", 45, Bake.GOLDEN),
    Cookie("c2", 90, Bake.RAW),
    Cookie("c3", 50, Bake.GOLDEN),
    Cookie("c4", 80, Bake.BURNT),
    Cookie("c5", 30, Bake.GOLDEN),
)

/** Two golden cookies for a lunchbox, picked by a List chain and by a Sequence. Predict the print order first. */
fun main() {
    println("List chain:")
    val eager = tray
        .filter { println("  filter ${it.id}"); it.bake == Bake.GOLDEN }
        .map { println("  map ${it.id}"); it.grams }
        .take(2)
    println("  lunchbox $eager")

    println("Sequence chain:")
    val lazy = tray.asSequence()
        .filter { println("  filter ${it.id}"); it.bake == Bake.GOLDEN }
        .map { println("  map ${it.id}"); it.grams }
        .take(2)
    println("  built ${lazy::class.simpleName}, nothing has run yet")
    println("  lunchbox ${lazy.toList()}")
}
