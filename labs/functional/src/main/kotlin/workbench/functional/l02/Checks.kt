package workbench.functional.l02

/** One dish the host might cook. diet is "vegan", "vegetarian" or "meat"; main is its main ingredient. */
data class Dish(val name: String, val minutes: Int, val diet: String, val main: String)

/** Why a dish doesn't suit a guest: which check said no, and about which dish. */
data class Problem(val check: String, val dish: String)

/** A check looks at one dish. It returns a Problem, or null when the dish passes. */
typealias Check = (Dish) -> Problem?

val MEAT_FREE_DIETS = setOf("vegan", "vegetarian")
val IN_SEASON = setOf("pumpkin", "apple", "leek", "mushroom")      // an autumn kitchen

/**
 * TODO 1: return a check that rejects dishes taking longer than [maxMinutes], with check name "too-slow".
 * A dish of exactly maxMinutes passes. The lambda you return captures maxMinutes: that's a closure.
 */
fun readyWithin(maxMinutes: Int): Check = TODO("return a lambda that compares it.minutes with maxMinutes")

/**
 * TODO 2: a check written as a lambda value. Reject dishes whose diet is not in MEAT_FREE_DIETS,
 * with check name "has-meat".
 */
val meatFree: Check = { TODO("check it.diet against MEAT_FREE_DIETS") }

/** TODO 3a: an ordinary function. Reject dishes whose main ingredient is not in IN_SEASON, with check name "out-of-season". */
fun inSeason(dish: Dish): Problem? = TODO("an ordinary if expression")

/** TODO 3b: make this a function reference to inSeason instead of a lambda. */
val seasonCheck: Check = { TODO("replace this lambda with ::inSeason") }

/**
 * TODO 4: run [checks] in order and return the first problem, or null if every check passes.
 * Stop at the first problem: later checks must not run (some of them phone a guest).
 */
fun firstProblem(dish: Dish, checks: List<Check>): Problem? = TODO("loop, or look for firstNotNullOfOrNull")

/** TODO 5: run every check and return all the problems, in check order. */
fun allProblems(dish: Dish, checks: List<Check>): List<Problem> = TODO("every non-null result")

/**
 * TODO 6: does the dish suit a guest? Returns true when it passes every check. When it doesn't, call
 * [onProblem] with the first problem (if a callback was given) and return false.
 * onProblem has a nullable function type: callers may leave it out.
 */
fun suits(dish: Dish, checks: List<Check>, onProblem: ((Problem) -> Unit)? = null): Boolean =
    TODO("firstProblem, then onProblem?.invoke(...)")
