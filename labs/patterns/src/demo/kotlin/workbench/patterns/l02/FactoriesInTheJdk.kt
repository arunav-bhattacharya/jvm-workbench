package workbench.patterns.l02

import java.time.Duration
import java.util.EnumSet
import java.util.concurrent.TimeUnit

// The same JDK factories called from Kotlin, plus Kotlin's own. Predict each class name first.

fun main() {
    // JDK static factories pick an implementation from the input
    println("List.of(1)            -> " + java.util.List.of(1).javaClass.simpleName)
    println("List.of(1, 2, 3)      -> " + java.util.List.of(1, 2, 3).javaClass.simpleName)
    println("EnumSet of TimeUnit   -> " + EnumSet.noneOf(TimeUnit::class.java).javaClass.simpleName +
            " (" + TimeUnit.entries.size + " constants)")
    println("EnumSet of scripts    -> " + EnumSet.noneOf(Character.UnicodeScript::class.java).javaClass.simpleName +
            " (" + Character.UnicodeScript.entries.size + " constants)")

    // Kotlin's factory functions do the same (full names, since two of these are nested classes)
    println("listOf()              -> " + listOf<Int>().javaClass.name)
    println("listOf(1)             -> " + listOf(1).javaClass.name)
    println("listOf(1, 2, 3)       -> " + listOf(1, 2, 3).javaClass.name)

    // a factory can hand back a cached instance, and its name says what you get
    println("Currency EUR twice    -> same object? " + (java.util.Currency.getInstance("EUR") === java.util.Currency.getInstance("EUR")))
    println("Duration.ofMinutes(2) -> " + Duration.ofMinutes(2))
}
