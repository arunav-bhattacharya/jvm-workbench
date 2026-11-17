package workbench.generics.l08.demo

inline fun <reified T : Any> classOf(x: T) = x::class          // T : Any, so x can't be null

fun main() {
    // 1. Reified T is the outer class only. Nested type arguments are still erased.
    val boxes: List<Any> = listOf(listOf(180, 150), listOf("Gala"), "Fuji")
    val nameLists = boxes.filterIsInstance<List<String>>()     // compiles with no warning at all
    println("lists of names? $nameLists")

    // 2. With a non-null bound, x::class is fine.
    println("classOf(\"Gala\") = ${classOf("Gala").simpleName}")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // val nothing = classOf<Nothing>(TODO())                   // 1
    // val n: String = nameLists[0][0]                          // 2 (compiles: what happens at run time?)
}

// 3. Kotlin 2.4 turned this into an error: T may be nullable, and null has no class.
// inline fun <reified T> klassOf(x: T) = x::class
