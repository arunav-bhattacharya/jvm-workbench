package workbench.generics.l06.demo

/**
 * The Kotlin docs' copy example. Array is invariant, because it has get AND set.
 * This function only reads `from`, so it asks for an out-projection of it.
 */
fun copyRow(from: Array<out Any>, to: Array<Any>) {
    for (i in from.indices) to[i] = from[i]      // get() on Array<out Any> returns Any: fine
    // from[0] = "EUR"                          // wrong move 2: an out-projection has no set()
}

fun main() {
    val amounts: Array<Int> = arrayOf(1_200, 350, 99)
    val row = Array<Any>(3) { "" }
    copyRow(amounts, row)                        // Array<Int> fits Array<out Any>
    println(row.joinToString())

    // Wrong move 1: without a projection, Array<Int> is not an Array<Any>.
    // val strict: Array<Any> = amounts

    // Wrong move 3: the bug Java only finds at run time. Kotlin stops it here.
    // copyRow(amounts, arrayOfNulls<String>(3))
}
