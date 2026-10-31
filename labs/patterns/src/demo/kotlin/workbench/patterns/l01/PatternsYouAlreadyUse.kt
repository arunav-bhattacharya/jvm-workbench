package workbench.patterns.l01

import java.util.Collections
import java.util.Currency

// Five patterns hiding in the JDK and the Kotlin standard library. Predict each line before you run it.

private data class Payment(val id: String, val amountMinor: Long)

fun main() {
    // Singleton: one Runtime per JVM, no public constructor
    println("1. Runtime is a singleton:      " + (Runtime.getRuntime() === Runtime.getRuntime()))

    // Flyweight: a nullable Int is a boxed java.lang.Integer, and Integer.valueOf caches -128..127
    val a: Int? = 127; val b: Int? = 127; val c: Int? = 128; val d: Int? = 128
    println("2. 127 === 127 (boxed):         " + (a as Any === b as Any))
    println("3. 128 === 128 (boxed):         " + (c as Any === d as Any))
    println("4. EUR === EUR (Currency):      " + (Currency.getInstance("EUR") === Currency.getInstance("EUR")))

    // Proxy/decorator view: unmodifiableList reads through to the list it wraps
    val ids = mutableListOf("p-1")
    val view: List<String> = Collections.unmodifiableList(ids)
    ids += "p-2"
    println("5. view after ids += \"p-2\":     $view")

    // Strategy: a Comparator is an algorithm you pass in; compareByDescending builds one from a lambda
    val payments = listOf(Payment("p-9", 500), Payment("p-3", 12_000))
    println("6. sorted by amount, desc:      " + payments.sortedWith(compareByDescending { it.amountMinor }).map { it.id })
}
