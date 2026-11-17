package workbench.patterns.l10

// Walk the warehouse program's stock list lazily. The sequence builder writes the iterator's state machine.

data class StockPage(val items: List<String>, val next: Int?)

private val stockPages = mapOf(
    0 to StockPage(listOf("rye bread", "jam"), 1),
    1 to StockPage(emptyList(), 2),                     // an empty page in the middle
    2 to StockPage(listOf("tea"), null),
)

fun stock(fetch: (Int) -> StockPage): Sequence<String> = sequence {
    var cursor: Int? = 0
    while (cursor != null) {
        val page = fetch(cursor)                         // runs only when the consumer needs more
        yieldAll(page.items)
        cursor = page.next
    }
}

fun main() {
    val fetchPage = { cursor: Int -> println("  warehouse: sending page $cursor"); stockPages.getValue(cursor) }
    println("first two: ${stock(fetchPage).take(2).toList()}")
    println("all: ${stock(fetchPage).toList()}")
}
