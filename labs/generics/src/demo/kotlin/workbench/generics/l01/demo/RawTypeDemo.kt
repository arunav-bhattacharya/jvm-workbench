// Kotlin twin of RawTypeDemo.java. Kotlin has no raw types; the closest way to switch the checks off
// is an unchecked cast. The bad value goes in quietly and fails on the way out, exactly as in Java.
package workbench.generics.l01.demo

// MutableList<*> means "a list of something"; the cast pretends it is a list of anything
private fun legacyAppend(ids: MutableList<*>) {
    @Suppress("UNCHECKED_CAST")
    (ids as MutableList<Any?>).add(42)            // compiles; without @Suppress Kotlin warns
}

fun main() {
    val ids: MutableList<String> = mutableListOf()  // Kotlin infers nothing here: the type is declared
    ids.add("pay_1001")
    legacyAppend(ids)
    println("size = ${ids.size}, nothing failed yet")
    try {
        for (id in ids) {                           // the compiler inserted a cast to String here
            println(id.uppercase())
        }
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
    }
}
