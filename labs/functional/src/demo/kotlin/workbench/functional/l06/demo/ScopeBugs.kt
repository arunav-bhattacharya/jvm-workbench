package workbench.functional.l06.demo

enum class DishStage { PLANNED, COOKING }

data class Plate(val id: String, val servings: Int, val stage: DishStage)

class MiniMenu {
    private val onMenu = mutableSetOf<String>()
    /** Returns a slot id, or null when this dish is on the menu already. */
    fun add(p: Plate): String? = if (onMenu.add(p.id)) "slot-${p.id}" else null
}

fun planOpen(open: Plate?, menu: MiniMenu, suggest: () -> Plate): String? =
    open?.let { menu.add(it) } ?: run {
        println("    no dish open, downloading a suggestion")
        menu.add(suggest())
    }

class Timer { var minutes: Int = 0 }
class Tray { var minutes: Int = 0; val timer = Timer() }

data class Cake(val name: String, val tinId: String)
data class Tin(val name: String, val sizeCm: Int)

fun main() {
    val soup = Plate("d1", 4, DishStage.PLANNED)

    println("1. ?.let { } ?: run { }")
    val menu = MiniMenu()
    println("  first plan:  ${planOpen(soup, menu) { soup }}")
    println("  second plan: ${planOpen(soup, menu) { soup }}")

    println("2. also and apply drop the block's result")
    val cooking = soup.also { it.copy(stage = DishStage.COOKING) }
    println("  stage after also { copy }: ${cooking.stage}")
    val total = listOf(soup, soup).apply { sumOf { it.servings } }
    println("  total from apply { sumOf }: $total")

    println("3. nested apply")
    val tray = Tray().apply { timer.apply { minutes = 12 } }
    println("  tray.minutes = ${tray.minutes}, tray.timer.minutes = ${tray.timer.minutes}")

    println("4. nested it")
    val cakes = mapOf("k-1" to Cake("Lemon drizzle", "round-23"))
    val tins = mapOf("round-23" to Tin("springform", 23))
    val label = cakes["k-1"]?.let { tins[it.tinId]?.let { "${it.name}: ${it.sizeCm} cm tin" } }
    println("  label: $label")
}
