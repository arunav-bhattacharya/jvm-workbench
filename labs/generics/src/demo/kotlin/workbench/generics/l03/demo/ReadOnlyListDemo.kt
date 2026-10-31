package workbench.generics.l03.demo

/** Predict which lines compile. Uncomment ONE at a time and run. */
fun main() {
    val ms: MutableList<String> = mutableListOf("a")
    val ints: Array<Int> = arrayOf(1, 2)

    val la: List<Any> = ms                 // compiles: List is read-only and covariant
    println("as List<Any>: $la, first is a ${la[0]::class.simpleName}")

    // val ma: MutableList<Any> = ms       // 1
    // val anys: Array<Any> = ints         // 2
    // la.add(42)                          // 3
    // val back: List<String> = la         // 4
    println("ints: ${ints.joinToString()}")
}
