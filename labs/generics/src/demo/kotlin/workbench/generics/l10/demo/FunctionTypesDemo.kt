package workbench.generics.l10.demo

import java.math.BigDecimal

/** A new name for a function type. Not a new type: a Listener<E> IS an (E) -> Unit. */
typealias Listener<E> = (E) -> Unit

fun <A, B, C> andThen(first: (A) -> B, second: (B) -> C): (A) -> C = { a -> second(first(a)) }

fun fail(reason: String): Nothing = throw IllegalArgumentException(reason)

fun main() {
    // 1. Function1<in P, out R>: a more general second function fits.
    val toGrams: (String) -> Long = { BigDecimal(it).movePointRight(3).longValueExact() }   // kilograms to grams
    val describe: (Any) -> String = { "<$it>" }
    val pipeline: (String) -> CharSequence = andThen(toGrams, describe)
    println("pipeline(\"1.25\") = ${pipeline("1.25")}")

    // 2. Nothing is a subtype of every type.
    val none: List<Apple> = emptyList()                     // emptyList() is a List<Nothing> here
    val grams: Long = "x".toLongOrNull() ?: 0L
    val strict: Long = "180".toLongOrNull() ?: fail("not a number")   // fail returns Nothing, so this is a Long
    println("none = $none, grams = $grams, strict = $strict")

    // 3. A type alias is only a name.
    val signWriter: Listener<Apple> = { println("sign for ${it.name}") }
    val plain: (Apple) -> Unit = signWriter                 // same type, no conversion
    plain(Apple("Gala", 180))

    // Wrong move. Uncomment, predict the error, then run.
    // val tooStrict: (Any) -> String = andThen(toGrams, describe)
}
