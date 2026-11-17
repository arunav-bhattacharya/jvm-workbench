package workbench.functional.l02.demo

data class Dish(val name: String, val minutes: Int, val diet: String, val main: String, val nuts: Boolean = false)
data class Problem(val check: String, val dish: String)

// A check is a function from a dish to a problem, or null when the dish passes.
typealias Check = (Dish) -> Problem?

// Each check is a value: a lambda stored in a val, ready to go into a list.
val readyInAnHour: Check = { d -> if (d.minutes > 60) Problem("too-slow", d.name) else null }
val autumnOnly: Check = { d -> if (d.main in setOf("pumpkin", "leek", "apple", "mushroom")) null else Problem("out-of-season", d.name) }
val meatFree: Check = { d -> if (d.diet == "meat") Problem("has-meat", d.name) else null }

// Different guests get different lists. Adding a check for one guest changes nothing above.
val everyone: List<Check> = listOf(readyInAnHour, autumnOnly)
val forSam: List<Check> = everyone + meatFree             // Sam is vegetarian

// Run the checks in order and stop at the first problem.
fun firstProblem(d: Dish, checks: List<Check>): Problem? = checks.firstNotNullOfOrNull { check -> check(d) }

fun main() {
    val dishes = listOf(
        Dish("pumpkin soup", 40, "vegan", "pumpkin"),
        Dish("slow roast", 180, "meat", "beef"),
        Dish("leek and bacon tart", 50, "meat", "leek"),
        Dish("strawberry cake", 45, "vegetarian", "strawberry", nuts = true),
    )
    for (d in dishes) {
        val all = firstProblem(d, everyone)?.check ?: "ok"
        val sam = firstProblem(d, forSam)?.check ?: "ok"
        println("${d.name}: everyone=$all, Sam=$sam")
    }
}
