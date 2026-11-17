package workbench.generics.l09.demo

import kotlin.reflect.KClass

// The shop's fruit, used by the demos of this lesson (the Java twins use these Kotlin types too).
// Sealed, so that ReflectDemo can ask Fruit for its subclasses.
sealed interface Fruit { val name: String; val grams: Int }
data class Apple(override val name: String, override val grams: Int) : Fruit
data class Lemon(override val name: String, override val grams: Int) : Fruit

fun main() {
    val delivery: List<Fruit> = listOf(Apple("Gala", 180), Lemon("Eureka", 120))
    for (fruit in delivery) {
        val k: KClass<out Fruit> = fruit::class             // the class of SOME Fruit
        println("${fruit.name}: ${k.simpleName}, is an apple: ${k == Apple::class}")
    }

    val exact: KClass<Apple> = Apple::class                 // a class literal is exact
    val note: String? = delivery.firstOrNull()?.name
    val noteClass: KClass<out String>? = note?.let { it::class }  // no value, no class
    println("exact = ${exact.simpleName}, noteClass = ${noteClass?.simpleName}")

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // val strict: KClass<Fruit> = delivery[0]::class       // 1
    // val nullable = note::class                           // 2
    // val kn: KClass<String?>? = null                      // 3
}
