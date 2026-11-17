package workbench.generics.l09.demo

import kotlin.reflect.KClass
import kotlin.reflect.cast
import kotlin.reflect.safeCast

fun main() {
    val fruit: Fruit = Apple("Gala", 180)

    // 1. KClass <-> Class
    val k: KClass<Apple> = Apple::class
    val c: Class<Apple> = k.java
    println("k.java = ${c.simpleName}, c.kotlin == k: ${c.kotlin == k}, fruit.javaClass == c: ${fruit.javaClass == c}")

    // 2. checked is / as / as?
    println("isInstance: ${k.isInstance(fruit)}, cast(...).grams: ${k.cast(fruit).grams}, safeCast to Lemon: ${Lemon::class.safeCast(fruit)}")
    try {
        Lemon::class.cast(fruit)
    } catch (e: ClassCastException) {
        println("cast failed: ${e.message}")
    }

    // 3. names
    println("simpleName = ${k.simpleName}, qualifiedName = ${k.qualifiedName}")

    // 4. the primitive trap from lesson 8
    println("Int::class.java = ${Int::class.java}, Int::class.javaObjectType = ${Int::class.javaObjectType}")

    // Wrong move. Uncomment, predict the error, then run.
    // println(k.javaClass)
}
