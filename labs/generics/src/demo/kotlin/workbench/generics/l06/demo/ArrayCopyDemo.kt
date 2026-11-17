package workbench.generics.l06.demo

// The shop's fruit, used by every demo of this lesson (the Java twins use these Kotlin types too)
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name                 // prints as "Gala", not "Apple(name=Gala, grams=180)"
}
data class Lemon(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name
}

/**
 * The copy example from the Kotlin docs, in the shop. Array is invariant, because it has get AND set.
 * This function only reads `from`, so it asks for an out-projection of it: take-only, for this job.
 */
fun copyRow(from: Array<out Fruit>, to: Array<Fruit>) {
    for (i in from.indices) to[i] = from[i]      // get() on Array<out Fruit> returns Fruit: fine
    // from[0] = Lemon("Eureka", 95)             // wrong move 2: an out-projection has no set()
}

fun main() {
    val apples: Array<Apple> = arrayOf(Apple("Gala", 180), Apple("Fuji", 150))
    val window: Array<Fruit> = arrayOf(Lemon("Eureka", 120), Lemon("Eureka", 95))
    copyRow(apples, window)                      // Array<Apple> fits Array<out Fruit>
    println("window: ${window.joinToString()}")

    // Wrong move 1: without a projection, Array<Apple> is not an Array<Fruit>.
    // val strict: Array<Fruit> = apples

    // Wrong move 3: the bug Java only finds at run time. Kotlin stops it here.
    // copyRow(apples, arrayOfNulls<Lemon>(2))
}
