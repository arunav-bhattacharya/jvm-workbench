// Kotlin twin of RawTypeDemo.java. Kotlin has no raw types; the closest way to switch the checks off
// is an unchecked cast. The bad value goes in quietly and fails on the way out, exactly as in Java.
package workbench.generics.l01.demo

// MutableList<*> means "a list of something"; the cast pretends it is a list of anything
private fun addOldStock(names: MutableList<*>) {
    @Suppress("UNCHECKED_CAST")
    (names as MutableList<Any?>).add(42)            // compiles; without @Suppress Kotlin warns
}

fun main() {
    val varieties: MutableList<String> = mutableListOf()   // the type is declared, nothing to infer
    varieties.add("Gala")
    addOldStock(varieties)
    println("size = ${varieties.size}, nothing failed yet")
    try {
        for (variety in varieties) {                // the compiler inserted a cast to String here
            println(variety.uppercase())
        }
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
    }
}
