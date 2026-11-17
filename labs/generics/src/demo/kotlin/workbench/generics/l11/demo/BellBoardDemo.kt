package workbench.generics.l11.demo

import kotlin.reflect.KClass
import kotlin.reflect.safeCast

// The shop's fruit, used by the demos of this lesson (the Java twins use these Kotlin types too)
interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
data class Lemon(override val name: String, override val grams: Int) : Fruit

/** The smallest typed bell board: one list of adapters, each of which checks the item's class. */
class Bells {
    private val adapters = mutableListOf<(Fruit) -> Unit>()

    fun <E : Fruit> listen(type: KClass<E>, listener: (E) -> Unit) {
        // adapters.add(listener)                                    // wrong move 1
        adapters.add { item -> type.safeCast(item)?.let(listener) }  // takes any fruit, passes on only an E
    }

    fun ring(item: Fruit) = adapters.forEach { it(item) }
}

fun main() {
    val bells = Bells()
    val stockCount: (Fruit) -> Unit = { println("stock: one more ${it.name}") }
    bells.listen(Apple::class) { println("sign for ${it.name}, ${it.grams} g") }
    bells.listen(Apple::class, stockCount)          // a listener for the supertype fits: in P
    bells.listen(Lemon::class) { println("lemon tray: ${it.name}") }

    bells.ring(Apple("Gala", 180))                  // items flow out of the delivery...
    bells.ring(Lemon("Eureka", 120))                // ...and into the listeners that accept them

    // Wrong move 2. Uncomment, predict the error, then run.
    // bells.listen(Fruit::class) { a: Apple -> println(a.name) }
}
