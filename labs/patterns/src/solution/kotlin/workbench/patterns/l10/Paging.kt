package workbench.patterns.l10

data class Page(val items: List<String>, val next: Int?)

fun pagedSequence(fetch: (cursor: Int) -> Page): Sequence<String> = sequence {
    var cursor: Int? = 0
    while (cursor != null) {             // a plain loop: the compiler turns it into the iterator's state machine
        val page = fetch(cursor)         // runs only when the consumer asks for an item past the current page
        yieldAll(page.items)             // an empty page yields nothing, and the loop moves on
        cursor = page.next
    }
}
