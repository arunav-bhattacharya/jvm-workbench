package workbench.generics.l03.demo

/** What would go wrong if MutableList<String> were a MutableList<Any>? Bypass the check and see. */
fun main() {
    val ids: MutableList<String> = mutableListOf("pay_1")

    // Step 1: uncomment this line and run. The compiler refuses it.
    // val view: MutableList<Any> = ids

    // Step 2: force it with an unchecked cast. This compiles, with a warning.
    @Suppress("UNCHECKED_CAST")
    val anything = ids as MutableList<Any>
    anything.add(42)                       // fine for a MutableList<Any>
    println("ids has ${ids.size} elements, and nothing failed yet")

    try {
        val second: String = ids[1]        // the compiler inserted a cast to String here
        println("second id: $second")
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
    }
}
