package workbench.generics.l04

// out T: items is a List<T> val (out-position), and map's parameter (T) -> R puts T in the
// parameter of a parameter: two flips, so T is still only coming out.
data class Page<out T>(val items: List<T>, val nextCursor: String?) {

    fun <R> map(f: (T) -> R): Page<R> = Page(items.map(f), nextCursor)
}

fun firstOnPage(page: Page<Payment>): Payment? = page.items.firstOrNull()
