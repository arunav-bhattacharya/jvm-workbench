package workbench.generics.l04

// out T: Dispenser only ever hands T values out, so a Dispenser<Apple> can safely act as a Dispenser<Fruit>
class Dispenser<out T>(items: List<T>) {
    private val queue = ArrayDeque(items)

    // `var lastServed: T?` with a private setter is still a var: its type sits in an invariant position.
    // Split it: a private var (exempt) and a public val (an out-position).
    private var last: T? = null
    val lastServed: T? get() = last

    fun hasNext(): Boolean = queue.isNotEmpty()

    fun next(): T {
        if (queue.isEmpty()) throw NoSuchElementException("dispenser is empty")
        val item = queue.removeFirst()
        last = item
        return item
    }
}

// an extension owns its T, so taking a T parameter is fine here
fun <T> Dispenser<T>.nextOr(fallback: T): T = if (hasNext()) next() else fallback

fun drainAll(dispenser: Dispenser<Fruit>): List<Fruit> {
    val out = ArrayList<Fruit>()
    while (dispenser.hasNext()) out.add(dispenser.next())
    return out
}

fun totalGrams(dispenser: Dispenser<Fruit>): Int = drainAll(dispenser).sumOf { it.grams }
