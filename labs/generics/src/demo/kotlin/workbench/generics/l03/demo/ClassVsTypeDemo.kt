package workbench.generics.l03.demo

/** Classes are what exists at run time. Types are what the compiler checks. They are not the same thing. */
fun main() {
    val ids: MutableList<String> = mutableListOf("pay_1")
    val amounts: MutableList<Int> = mutableListOf(1200)

    // the JVM sees one class for both lists
    println("same runtime class:  ${ids.javaClass == amounts.javaClass}  (${ids.javaClass.name})")
    // Kotlin's List and MutableList are one JVM interface, java.util.List
    println("MutableList::class == List::class:  ${MutableList::class == List::class}")
    println("MutableList::class.java:  ${MutableList::class.java}")

    // String and String? are two types of one class
    val maybe: String? = ids.firstOrNull()
    val sure: String = "EUR"
    val widened: String? = sure       // String is a subtype of String?: always fine
    println("String? holds '$maybe', widened from String holds '$widened'")

    // Wrong moves. Uncomment ONE at a time, predict the error, then run.
    // val narrowed: String = maybe
    // val k = String?::class
}
