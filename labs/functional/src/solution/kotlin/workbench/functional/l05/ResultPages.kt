package workbench.functional.l05

fun interface RecipeSite {
    fun page(number: Int): List<Recipe>
}

fun allResults(site: RecipeSite): Sequence<Recipe> = sequence {
    var number = 0
    while (true) {
        val page = site.page(number++)         // runs only when the consumer wants the next recipe
        if (page.isEmpty()) break              // an empty page ends the sequence
        yieldAll(page)                         // pauses here between recipes
    }
}
