package workbench.generics.l02.demo

import java.time.LocalDate

interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
data class Lemon(override val name: String, override val grams: Int) : Fruit

/** The bound T : Fruit means "T is Fruit or a subtype of it", so .grams is allowed. */
fun <T : Fruit> heavier(a: T, b: T): T = if (a.grams >= b.grams) a else b

/** The bound T : Comparable<T> means "T can be compared with another T", so > is allowed. */
fun <T : Comparable<T>> maxOf2(a: T, b: T): T = if (a > b) a else b

fun main() {
    val apple: Apple = heavier(Apple("Gala", 180), Apple("Fuji", 150))   // two apples in, an Apple out
    println(apple)
    println(maxOf2(180, 150))
    println(maxOf2("Gala", "Fuji"))
    println(maxOf2(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 10, 30)))

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // println(heavier("Gala", "Fuji"))
    // println(maxOf2(1, "a"))
    // println(maxOf2(Apple("Gala", 180), Apple("Fuji", 150)))
}
