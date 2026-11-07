package workbench.generics.l07.demo

/** Logs any list. It never cares what the elements are, so it says `*`. */
fun logAll(items: List<*>) {
    for (item in items) println("  $item")      // each item is Any?
}

/** Empties any buffer. clear() takes no element, so a star projection allows it. */
fun reset(buffer: MutableList<*>): Int {
    val n = buffer.size
    buffer.clear()
    return n
}

fun main() {
    val ids: MutableList<String> = mutableListOf("pay_1", "pay_2")
    val cents: MutableList<Int> = mutableListOf(1_200, 350, 99)
    logAll(ids)
    logAll(cents)

    val star: MutableList<*> = ids
    val first: Any? = star[0]                   // reading gives Any?
    println("first = $first, removed ${reset(ids)} ids and ${reset(cents)} amounts")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // star.add("pay_3")                        // 1
    // star.add(null)                           // 2
    // val id: String = star[0]                 // 3
}
