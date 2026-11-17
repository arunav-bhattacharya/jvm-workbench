package workbench.generics.l03.demo

// The shop's fruit, used by every Kotlin demo of this lesson
interface Fruit { val name: String }
data class Apple(override val name: String) : Fruit
data class Lemon(override val name: String) : Fruit

/** What would go wrong if a crate of apples could be used as a crate of any fruit? Bypass the check and see. */
fun main() {
    val apples: MutableList<Apple> = mutableListOf(Apple("Gala"))

    // Step 1: uncomment this line and run. The compiler refuses it.
    // val view: MutableList<Fruit> = apples

    // Step 2: force it with an unchecked cast. This compiles, with a warning.
    @Suppress("UNCHECKED_CAST")
    val anyFruit = apples as MutableList<Fruit>
    anyFruit.add(Lemon("Eureka"))              // fine for a crate of any fruit
    println("the apple crate holds ${apples.size} items, and nothing failed yet")

    try {
        val second: Apple = apples[1]          // the compiler inserted a cast to Apple here
        println("second apple: ${second.name}")
    } catch (e: ClassCastException) {
        println("ClassCastException: ${e.message}")
    }
}
