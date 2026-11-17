package workbench.functional.l05.demo

data class SearchResult(val title: String, val minutes: Int)

/** Stands for one web request to the recipe site: three results per page, quicker recipes on later pages. */
private fun fetchPage(page: Int): List<SearchResult> {
    println("  fetching page $page")
    return List(3) { i -> SearchResult("R$page-$i", 60 - (page * 3 + i) * 5) }
}

fun main() {
    // 1. a paging source: the block runs only as far as the consumer pulls
    val results = sequence {
        for (page in 1..3) yieldAll(fetchPage(page))
    }
    println("first recipe under 30 minutes:")
    println("  ${results.first { it.minutes < 30 }}")

    // 2. the app's serving buttons: start at 1, double, and stop when the lambda returns null
    val servings = generateSequence(1) { (it * 2).takeIf { next -> next <= 16 } }
    println("servings: ${servings.toList()}")
}
