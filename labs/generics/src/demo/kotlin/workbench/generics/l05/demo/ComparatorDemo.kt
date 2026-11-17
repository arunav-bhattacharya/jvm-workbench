package workbench.generics.l05.demo

/** One comparator, written for all fruit, sorts lists of apples and lists of lemons. */
val byWeight: Comparator<Fruit> = compareBy { it.grams }

fun main() {
    val apples = listOf(Apple("Gala", 180), Apple("Fuji", 150))
    val lemons = listOf(Lemon("Eureka", 120), Lemon("Eureka", 95))

    // sortedWith takes a Comparator<in T>: a comparator of T or of any supertype of T
    println(apples.sortedWith(byWeight).map { "${it.name} ${it.grams} g" })
    println(lemons.sortedWith(byWeight).map { "${it.name} ${it.grams} g" })

    val forApples: Comparator<in Apple> = byWeight     // fine with a use-site `in`

    // Wrong move. Uncomment, predict the error, then run.
    // val strict: Comparator<Apple> = byWeight
    println("forApples compares Gala with Fuji: ${forApples.compare(apples[0], apples[1])}")
}
