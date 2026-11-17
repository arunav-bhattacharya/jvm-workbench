package workbench.generics.l08.demo

// The shop's fruit, used by the demos of this lesson (the Java twins use these Kotlin types too)
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name                 // prints as "Gala", not "Apple(name=Gala, grams=180)"
}
data class Lemon(override val name: String, override val grams: Int) : Fruit {
    override fun toString() = name
}

/** inline copies the body into each caller; reified copies the caller's real T in with it. */
inline fun <reified T> Any?.isA(): Boolean = this is T

inline fun <reified T : Any> nameOf(): String = T::class.java.simpleName

fun main() {
    val delivery: List<Any?> = listOf(Apple("Gala", 180), "a paper bag", null, Lemon("Eureka", 120), Apple("Fuji", 150))

    println("Gala isA<Apple>() = ${delivery[0].isA<Apple>()}, the bag isA<Apple>() = ${delivery[1].isA<Apple>()}")
    println("apples: ${delivery.filterIsInstance<Apple>()}")     // the standard library's reified filter
    println("lemons: ${delivery.filterIsInstance<Lemon>()}")
    println("nameOf<Lemon>() = ${nameOf<Lemon>()}")
}

// Wrong moves. Uncomment one at a time, predict the error, then run.
// fun <reified T> notInline(x: Any) = x is T          // 1
// fun <T> forward(x: Any) = x.isA<T>()               // 2
