package workbench.generics.l07.demo

/** Prints any list. It never cares what the elements are, so it says `*`. */
fun printAll(items: List<*>) {
    for (item in items) println("  $item")      // each item is Any?
}

/** Empties any crate. clear() takes no element, so a star projection allows it. */
fun empty(crate: MutableList<*>): Int {
    val n = crate.size
    crate.clear()
    return n
}

fun main() {
    val varieties: MutableList<String> = mutableListOf("Gala", "Fuji")
    val weights: MutableList<Int> = mutableListOf(180, 150, 120)
    printAll(varieties)
    printAll(weights)

    val unlabeled: MutableList<*> = varieties
    val first: Any? = unlabeled[0]              // reading gives Any?
    println("first = $first, emptied ${empty(varieties)} names and ${empty(weights)} weights")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // unlabeled.add("Eureka")                  // 1
    // unlabeled.add(null)                      // 2
    // val name: String = unlabeled[0]          // 3
}
