package workbench.generics.l08.demo

inline fun <reified T : Any> classOf(x: T) = x::class          // T : Any, so x can't be null

fun main() {
    // 1. Reified T is the outer class only. Nested type arguments are still erased.
    val batches: List<Any> = listOf(listOf(1_200, 350), listOf("pay_1"), "pay_2")
    val stringLists = batches.filterIsInstance<List<String>>()  // compiles with no warning at all
    println("lists of strings? $stringLists")

    // 2. With a non-null bound, x::class is fine.
    println("classOf(\"pay_1\") = ${classOf("pay_1").simpleName}")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // val nothing = classOf<Nothing>(TODO())                    // 1
    // val n: String = stringLists[0][0]                         // 2 (compiles: what happens at run time?)
}

// 3. Kotlin 2.4 turned this into an error: T may be nullable, and null has no class.
// inline fun <reified T> klassOf(x: T) = x::class
