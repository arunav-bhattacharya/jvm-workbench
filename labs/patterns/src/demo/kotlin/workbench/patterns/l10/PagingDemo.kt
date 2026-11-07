package workbench.patterns.l10

// Walk a cursor-paginated refunds API lazily. The sequence builder writes the iterator's state machine.

data class RefundPage(val items: List<String>, val next: Int?)

private val refundPages = mapOf(
    0 to RefundPage(listOf("rf_1", "rf_2"), 1),
    1 to RefundPage(emptyList(), 2),                    // an empty page in the middle
    2 to RefundPage(listOf("rf_3"), null),
)

fun refunds(fetch: (Int) -> RefundPage): Sequence<String> = sequence {
    var cursor: Int? = 0
    while (cursor != null) {
        val page = fetch(cursor)                         // runs only when the consumer needs more
        yieldAll(page.items)
        cursor = page.next
    }
}

fun main() {
    val fetchPage = { cursor: Int -> println("  GET /refunds?cursor=$cursor"); refundPages.getValue(cursor) }
    println("first two: ${refunds(fetchPage).take(2).toList()}")
    println("all: ${refunds(fetchPage).toList()}")
}
