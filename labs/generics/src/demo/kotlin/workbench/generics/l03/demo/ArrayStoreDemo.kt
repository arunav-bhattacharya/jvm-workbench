// Kotlin twin of ArrayStoreDemo.java. Kotlin arrays are invariant, so you need a cast to reach
// the same trap. Once you do, the JVM's store check fires exactly as it does for Java.
package workbench.generics.l03.demo

fun main() {
    val currencies: Array<String> = arrayOf("EUR", "USD")

    // Step 2: uncomment the next line and run. Kotlin refuses it: arrays are invariant.
    // val refused: Array<Any> = currencies

    val objects = currencies as Array<Any>     // forced: at run time a String[] really is an Object[]
    try {
        objects[0] = 978                        // compiles: an Int is an Any
        println("stored 978")
    } catch (e: ArrayStoreException) {
        println("ArrayStoreException: ${e.message}")
    }
    println("currencies[0] is still ${currencies[0]}")
}
