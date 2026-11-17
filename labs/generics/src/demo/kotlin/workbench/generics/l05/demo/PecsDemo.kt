package workbench.generics.l05.demo

/** Copy from a producer into a consumer: `from` only gives T, `to` only takes T. */
fun <T> copyInto(from: List<T>, to: MutableList<in T>) {   // List is already out; MutableList gets a use-site in
    for (x in from) to.add(x)
}

fun main() {
    val apples: List<Apple> = listOf(Apple("Gala", 180), Apple("Fuji", 150))
    val shelf: MutableList<Fruit> = mutableListOf(Lemon("Eureka", 120))
    val anything: MutableList<Any> = mutableListOf("a paper bag")

    copyInto(apples, shelf)           // T = Apple; a MutableList<Fruit> accepts apples
    copyInto(apples, anything)
    println("shelf = $shelf, anything = $anything")

    // Wrong move. Uncomment, predict the error, then run.
    // copyInto(shelf, mutableListOf<Apple>())
}
