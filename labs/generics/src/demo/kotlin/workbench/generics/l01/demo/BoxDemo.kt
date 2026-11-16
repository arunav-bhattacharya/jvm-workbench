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
    val variety = Box("Gala")          // Box<String>
    val count = Box(12)                // Box<Int>
    val old = variety.replace("Fuji")
    println("variety was $old, now ${variety.value}")
    println("count is ${count.value}")
    println("first on the list: ${firstOrNull(listOf("Gala", "Fuji"))}")

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // count.replace("Fuji")
    // val wrong: Box<String> = Box(42)
    // val first: String = firstOrNull(listOf("Gala"))
}
