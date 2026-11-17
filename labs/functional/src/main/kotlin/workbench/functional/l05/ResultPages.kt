package workbench.functional.l05

/**
 * A recipe website's search results, one page at a time. Pages are numbered from 0. Each call is a
 * web request, and an empty page means there are no more results.
 */
fun interface RecipeSite {
    fun page(number: Int): List<Recipe>
}

/**
 * Every result the site holds, page after page, as a lazy [Sequence]. Build it with `sequence { }`:
 * - fetch nothing until someone asks for the first recipe;
 * - fetch page n + 1 only once every recipe of page n has been handed out;
 * - stop at the first empty page, and never ask for the page after it.
 */
fun allResults(site: RecipeSite): Sequence<Recipe> =
    TODO("sequence { ... yieldAll(page) ... }")
