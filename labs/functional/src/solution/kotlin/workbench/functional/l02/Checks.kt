package workbench.functional.l02

/** One dish the host might cook. diet is "vegan", "vegetarian" or "meat"; main is its main ingredient. */
data class Dish(val name: String, val minutes: Int, val diet: String, val main: String)

/** Why a dish doesn't suit a guest: which check said no, and about which dish. */
data class Problem(val check: String, val dish: String)

/** A check looks at one dish. It returns a Problem, or null when the dish passes. */
typealias Check = (Dish) -> Problem?

val MEAT_FREE_DIETS = setOf("vegan", "vegetarian")
val IN_SEASON = setOf("pumpkin", "apple", "leek", "mushroom")      // an autumn kitchen

// A closure: the returned lambda keeps maxMinutes alive after readyWithin has returned.
fun readyWithin(maxMinutes: Int): Check = { d ->
    if (d.minutes > maxMinutes) Problem("too-slow", d.name) else null
}

// A lambda stored in a val. It captures nothing, so it compiles to one shared instance.
val meatFree: Check = { d ->
    if (d.diet in MEAT_FREE_DIETS) null else Problem("has-meat", d.name)
}

fun inSeason(dish: Dish): Problem? =
    if (dish.main in IN_SEASON) null else Problem("out-of-season", dish.name)

// A function reference: the type (Dish) -> Problem? matches, so it IS a Check.
val seasonCheck: Check = ::inSeason

// firstNotNullOfOrNull is inline and stops at the first non-null result, so later checks never run.
fun firstProblem(dish: Dish, checks: List<Check>): Problem? =
    checks.firstNotNullOfOrNull { check -> check(dish) }

fun allProblems(dish: Dish, checks: List<Check>): List<Problem> =
    checks.mapNotNull { check -> check(dish) }

fun suits(dish: Dish, checks: List<Check>, onProblem: ((Problem) -> Unit)? = null): Boolean {
    val problem = firstProblem(dish, checks) ?: return true
    onProblem?.invoke(problem)          // a nullable function type is called with ?.invoke
    return false
}
