package workbench.generics.l07

fun describe(value: Any?): String = when (value) {
    null -> "nothing"
    is String -> "text $value"
    is List<*> -> "list of ${value.size}"          // `is List<String>` would not compile: erased
    is Map<*, *> -> "map of ${value.size}"         // one star per type parameter
    is Number -> "number $value"
    else -> "other"
}

fun stringsIn(value: Any?): List<String> {
    if (value !is List<*>) return emptyList()
    val out = ArrayList<String>()
    for (e in value) if (e is String) out += e      // each element is Any?: check it, then it smart-casts
    return out
}

// MutableList<*>: "a mutable list of some element type". clear() takes no element, so it is allowed.
fun drain(buffer: MutableList<*>): Int {
    val n = buffer.size
    buffer.clear()
    return n
}
