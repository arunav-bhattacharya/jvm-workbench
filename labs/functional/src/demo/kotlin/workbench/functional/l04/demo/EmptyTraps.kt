package workbench.functional.l04.demo

// Runs one expression and prints its value, or the exception it threw.
fun attempt(label: String, block: () -> Any?) {
    val result = try {
        block().toString()
    } catch (e: Exception) {
        "throws $e"
    }
    println("%-32s %s".format(label, result))
}

fun main() {
    val none = emptyList<Int>()                        // a day when nothing was baked
    attempt("fold(0) { a, b -> a + b }") { none.fold(0) { a, b -> a + b } }
    attempt("sum()") { none.sum() }
    attempt("reduceOrNull { a, b -> a + b }") { none.reduceOrNull { a, b -> a + b } }
    attempt("reduce { a, b -> a + b }") { none.reduce { a, b -> a + b } }
    attempt("first()") { none.first() }
    attempt("firstOrNull()") { none.firstOrNull() }
    attempt("maxOf { it }") { none.maxOf { it } }
    attempt("maxOrNull()") { none.maxOrNull() }
}
