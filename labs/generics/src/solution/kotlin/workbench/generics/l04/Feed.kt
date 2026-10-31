package workbench.generics.l04

// out T: Feed only ever hands T values out, so a Feed<CardPayment> can safely act as a Feed<Payment>
class Feed<out T>(items: List<T>) {
    private val queue = ArrayDeque(items)

    // `var lastServed: T?` with a private setter is still a var: its type sits in an invariant position.
    // Split it: a private var (exempt) and a public val (an out-position).
    private var last: T? = null
    val lastServed: T? get() = last

    fun hasNext(): Boolean = queue.isNotEmpty()

    fun next(): T {
        if (queue.isEmpty()) throw NoSuchElementException("feed is empty")
        val item = queue.removeFirst()
        last = item
        return item
    }
}

// an extension owns its T, so taking a T parameter is fine here
fun <T> Feed<T>.nextOr(fallback: T): T = if (hasNext()) next() else fallback

fun drainAll(feed: Feed<Payment>): List<Payment> {
    val out = ArrayList<Payment>()
    while (feed.hasNext()) out.add(feed.next())
    return out
}

fun totalCents(feed: Feed<Payment>): Long = drainAll(feed).sumOf { it.cents }
