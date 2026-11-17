package workbench.generics.l03.demo

/** Predict which lines compile. Uncomment ONE at a time and run. (Fruit, Apple, Lemon: see InvarianceDemo.kt.) */
fun main() {
    val crate: MutableList<Apple> = mutableListOf(Apple("Gala"))
    val weights: Array<Int> = arrayOf(180, 150)

    val display: List<Fruit> = crate          // compiles: List is read-only and covariant
    println("as List<Fruit>: $display, first is a ${display[0]::class.simpleName}")

    // val anyCrate: MutableList<Fruit> = crate   // 1
    // val anys: Array<Any> = weights             // 2
    // display.add(Lemon("Eureka"))               // 3
    // val back: List<Apple> = display            // 4
    println("weights: ${weights.joinToString()}")
}
