package workbench.generics.l04

/**
 * One page of results from a paginated API, such as "list payments for merchant M".
 *
 * TODO 1: make Page covariant: a Page<CardPayment> is a fine Page<Payment>. Add `out`.
 * Does `map` still compile after that? Predict first. (Its parameter has type (T) -> R.)
 * TODO 2: write map.
 */
data class Page<T>(val items: List<T>, val nextCursor: String?) {

    /** A page with [f] applied to every item, and the same cursor. */
    fun <R> map(f: (T) -> R): Page<R> = TODO("transform the items, keep the cursor")
}

/** The first payment on [page], or null when the page is empty. */
fun firstOnPage(page: Page<Payment>): Payment? = TODO("first item or null")
