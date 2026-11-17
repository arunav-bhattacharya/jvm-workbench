package workbench.functional.l05

/** One recipe in the app's big recipe book. */
data class Recipe(val id: Long, val title: String, val minutes: Int, val vegetarian: Boolean)

/**
 * Returns the first recipe in [book] whose match score is 90 or more, or null if there is none.
 *
 * [matchScore] stands for a call to the app's matching service, which rates from 0 to 100 how well a
 * recipe fits what is in your fridge. Each call takes about 2 ms, and the app pays for every one.
 * Score only as many recipes as you need: if the first good match is the 4,217th recipe in the book,
 * [matchScore] must run exactly 4,217 times.
 *
 * This version gives the right answer, but it scores the whole book before it looks for a match.
 * Fix it without changing the signature.
 */
fun firstMatch(book: List<Recipe>, matchScore: (Recipe) -> Int): Recipe? =
    book.map { it to matchScore(it) }
        .filter { (_, score) -> score >= 90 }
        .map { (recipe, _) -> recipe }
        .firstOrNull()

/**
 * Returns the ids of the first [n] vegetarian recipes that score 90 or more, in book order.
 * Fewer than [n] if the book runs out.
 *
 * Tonight's guest is vegetarian, so a quick look at the card comes first: never send a recipe that
 * isn't vegetarian to [matchScore]. And stop as soon as you have [n] ids: [matchScore] must not run
 * on any recipe after the nth match.
 */
fun firstMatchesFor(book: List<Recipe>, matchScore: (Recipe) -> Int, n: Int): List<Long> =
    TODO("filter, then score, then take(n), one recipe at a time")
