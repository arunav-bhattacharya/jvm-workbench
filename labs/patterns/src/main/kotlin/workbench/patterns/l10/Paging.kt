package workbench.patterns.l10

/** One page of a cursor-paginated PSP API. [next] is the cursor of the next page, or null on the last page. */
data class Page(val items: List<String>, val next: Int?)

/**
 * Every item of every page, starting at cursor 0, as a lazy sequence:
 *  - nothing is fetched until someone iterates;
 *  - a page is fetched only when the consumer needs an item from it;
 *  - an empty page is skipped (keep following `next`);
 *  - iteration ends after the page whose `next` is null.
 *
 * Build it with the `sequence {}` builder.
 */
fun pagedSequence(fetch: (cursor: Int) -> Page): Sequence<String> =
    TODO("sequence { ... } with a loop that follows the cursor")
