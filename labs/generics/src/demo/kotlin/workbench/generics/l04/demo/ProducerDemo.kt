package workbench.generics.l04.demo

// The shop's fruit, used by every demo of this lesson (the Java twins use these Kotlin types too)
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
data class Lemon(override val name: String, override val grams: Int) : Fruit

/** A producer: T only comes out. `out` tells the compiler so. */
interface Dispenser<out T> {
    fun next(): T?                     // null when it is empty
}

class ListDispenser<out T>(items: List<T>) : Dispenser<T> {
    private val it = items.iterator()
    override fun next(): T? = if (it.hasNext()) it.next() else null
}

/** Needs a Dispenser<Fruit>. Because Dispenser is `out`, a Dispenser<Apple> fits. */
fun totalGrams(dispenser: Dispenser<Fruit>): Int {
    var sum = 0
    while (true) {
        val fruit = dispenser.next() ?: break
        sum += fruit.grams
    }
    return sum
}

fun main() {
    val apples: Dispenser<Apple> = ListDispenser(listOf(Apple("Gala", 180), Apple("Fuji", 150)))
    println("apple total: ${totalGrams(apples)} g")       // a Dispenser<Apple> used as a Dispenser<Fruit>

    val anything: Dispenser<Any> = ListDispenser(listOf("a paper bag"))   // Dispenser<String> used as Dispenser<Any>
    println("first from anything: ${anything.next()}")
}
