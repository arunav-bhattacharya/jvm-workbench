package workbench.generics.l05.demo

// The shop's fruit, used by every demo of this lesson (the Java twins use these Kotlin types too)
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name                 // prints as "Gala", not "Apple(name=Gala, grams=180)"
}
data class Lemon(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name
}

/** A consumer: T only goes in. `in` tells the compiler so. */
interface Bin<in T> {
    fun drop(item: T)
}

/** The compost bin takes ANY fruit, and never hands anything back. */
class CompostBin : Bin<Fruit> {
    override fun drop(item: Fruit) = println("compost: $item, ${item.grams} g")
}

/** Needs somewhere to put bruised apples. Any bin that takes apples will do. */
fun throwOut(apples: List<Apple>, into: Bin<Apple>) {
    for (a in apples) into.drop(a)
}

fun main() {
    val compost: Bin<Fruit> = CompostBin()
    throwOut(listOf(Apple("Gala", 180), Apple("Fuji", 150)), compost)   // a Bin<Fruit> used as a Bin<Apple>

    val appleBin: Bin<Apple> = compost           // a Bin<Fruit> IS a Bin<Apple>
    appleBin.drop(Apple("Fuji", 140))

    // Wrong move. Uncomment, predict the error, then run.
    // val back: Bin<Fruit> = appleBin
}
