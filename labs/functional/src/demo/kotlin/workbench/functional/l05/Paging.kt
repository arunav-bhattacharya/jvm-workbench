package workbench.functional.l05

data class Settlement(val ref: String, val amountCents: Long)

/** Stands for one HTTP call to the acquirer: three pages of settlement records. */
private fun fetchPage(page: Int): List<Settlement> {
    println("  fetching page $page")
    return List(3) { i -> Settlement("S$page-$i", (page * 3 + i) * 1_000L) }
}

fun main() {
    // 1. a paging source: the block runs only as far as the consumer pulls
    val settlements = sequence {
        for (page in 1..3) yieldAll(fetchPage(page))
    }
    println("first settlement over 65.00:")
    println("  ${settlements.first { it.amountCents > 6_500 }}")

    // 2. a retry schedule: 100 ms doubling, and the sequence ends when the lambda returns null
    val backoff = generateSequence(100L) { (it * 2).takeIf { next -> next <= 1_600 } }
    println("backoff: ${backoff.toList()}")
}
