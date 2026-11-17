package workbench.generics.l07.demo

/** A supplier's delivery note, read from a text file, arrives as Any?. Find out what it is. */
fun shape(note: Any?): String = when (note) {
    null -> "empty"
    is Map<*, *> -> "a map with keys ${note.keys}"           // smart cast to Map<*, *>
    is List<*> -> "a list of ${note.size}"                   // smart cast to List<*>
    else -> "a single value: $note"
}

/** Safe: check every element instead of trusting the list's type. */
fun weightsIn(note: Any?): List<Int> {
    if (note !is List<*>) return emptyList()
    return note.mapNotNull { it as? Int }                    // as? gives null for anything that isn't an Int
}

fun main() {
    val note: Any? = mapOf("supplier" to "Hillside Orchard", "weights" to listOf(180, "bruised", 150))
    println(shape(note))
    println(shape(listOf(1, 2, 3)))
    println(shape(42))

    val weights = (note as Map<*, *>)["weights"]
    println("weights = ${weightsIn(weights)}")

    // Wrong move. Uncomment, predict the error, then run.
    // if (weights is List<Int>) println("a list of weights")
}
