// Kotlin twin of ArrayStoreDemo.java. Kotlin arrays are invariant, so you need a cast to reach
// the same trap. Once you do, the JVM's store check fires exactly as it does for Java.
// Fruit, Apple and Lemon are the classes declared in InvarianceDemo.kt.
package workbench.generics.l03.demo

fun main() {
    val crate: Array<Apple> = arrayOf(Apple("Gala"), Apple("Fuji"))

    // Step 2: uncomment the next line and run. Kotlin refuses it: arrays are invariant.
    // val refused: Array<Fruit> = crate

    @Suppress("UNCHECKED_CAST")
    val anyFruit = crate as Array<Fruit>        // forced: at run time an Apple[] really is a Fruit[]
    try {
        anyFruit[0] = Lemon("Eureka")           // compiles: a Lemon is a Fruit
        println("stored a lemon")
    } catch (e: ArrayStoreException) {
        println("ArrayStoreException: ${e.message}")
    }
    println("crate[0] is still ${crate[0].name}")
}
