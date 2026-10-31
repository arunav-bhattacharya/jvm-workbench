package workbench.generics.l01.demo

/** One class with one blank, T. Each use fills the blank with a real type. */
class Box<T>(var value: T) {
    /** Puts [newValue] in and returns the old value. Both have type T. */
    fun replace(newValue: T): T {
        val old = value
        value = newValue
        return old
    }
}

/** A generic function: <T> declares the blank, List<T> and T? use it. */
fun <T> firstOrNull(items: List<T>): T? = if (items.isEmpty()) null else items[0]

fun main() {
    val currency = Box("EUR")          // Box<String>
    val limit = Box(50_000L)           // Box<Long>
    val old = currency.replace("USD")
    println("currency was $old, now ${currency.value}")
    println("limit is ${limit.value}")
    println("first payment id: ${firstOrNull(listOf("pay_1", "pay_2"))}")

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // limit.replace("USD")
    // val wrong: Box<String> = Box(42)
    // val id: String = firstOrNull(listOf("pay_1"))
}
