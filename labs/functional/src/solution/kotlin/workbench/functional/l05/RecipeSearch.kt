package workbench.functional.l05

/** One recipe in the app's big recipe book. */
data class Recipe(val id: Long, val title: String, val minutes: Int, val vegetarian: Boolean)

fun firstMatch(book: List<Recipe>, matchScore: (Recipe) -> Int): Recipe? =
    book.asSequence()                          // one recipe at a time down the whole chain
        .map { it to matchScore(it) }
        .filter { (_, score) -> score >= 90 }
        .map { (recipe, _) -> recipe }
        .firstOrNull()                         // stops pulling after the first match
// book.firstOrNull { matchScore(it) >= 90 } is just as good: one inlined loop that also stops early.

fun firstMatchesFor(book: List<Recipe>, matchScore: (Recipe) -> Int, n: Int): List<Long> =
    book.asSequence()
        .filter { it.vegetarian }              // the quick look first, so other recipes never reach the service
        .filter { matchScore(it) >= 90 }
        .map { it.id }
        .take(n)                               // after n ids, nothing upstream is pulled again
        .toList()
