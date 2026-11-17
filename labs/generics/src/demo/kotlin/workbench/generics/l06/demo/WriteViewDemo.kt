package workbench.generics.l06.demo

/** Tops up a crate with [count] Gala apples. It only puts apples in, so any crate that takes apples will do. */
fun restock(crate: MutableList<in Apple>, count: Int) {
    repeat(count) { crate.add(Apple("Gala", 180)) }   // putting an Apple in: fine
    val first: Any? = crate.firstOrNull()             // reading compiles, but all you get is Any?
    println("  first is $first")
    // val firstApple: Apple = crate[0]                // wrong move 1: an in-projection can't promise an Apple
}

fun main() {
    val apples = mutableListOf(Apple("Fuji", 150))
    val fruit = mutableListOf<Fruit>(Lemon("Eureka", 120))
    val anything = mutableListOf<Any>("a paper bag")
    restock(apples, 1)
    restock(fruit, 2)
    restock(anything, 2)
    println("apples = $apples, fruit = $fruit, anything = $anything")

    java.util.Collections.fill(fruit, Apple("Fuji", 150))   // the JDK's fill(List<? super T> list, T obj)
    println("after Collections.fill: $fruit")

    // Wrong move 2: a crate of lemons can't take an apple.
    val lemons: MutableList<Lemon> = mutableListOf(Lemon("Eureka", 95))
    // restock(lemons, 1)
}
