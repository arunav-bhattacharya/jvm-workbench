package workbench.generics.l04.demo

/** Kotlin's List is declared List<out E>, so a List<Fruit> parameter accepts a List<Apple>. */
fun totalWeight(fruit: List<Fruit>): Int = fruit.sumOf { it.grams }

/** MutableList is invariant: this one only accepts a MutableList<Fruit>. */
fun totalWeightMutable(fruit: MutableList<Fruit>): Int = fruit.sumOf { it.grams }

fun main() {
    val apples: MutableList<Apple> = mutableListOf(Apple("Gala", 180), Apple("Fuji", 150))
    println("totalWeight(apples) = ${totalWeight(apples)}")

    // Wrong move. Uncomment, predict the error, then run.
    // println(totalWeightMutable(apples))
}
