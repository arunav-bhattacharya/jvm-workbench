package workbench.functional.l03.demo

import java.util.concurrent.ConcurrentHashMap

// A higher-order function that returns a function: same answers as f, but each one computed once.
fun <A : Any, R : Any> memoize(f: (A) -> R): (A) -> R {
    val cache = ConcurrentHashMap<A, R>()                 // captured: one cache per memoized function
    return { a -> cache.computeIfAbsent(a) { f(it) } }
}

// Pure but slow: imagine it searches a long food table on every call.
var tableLookups = 0
fun kcalPer100g(food: String): Int {
    tableLookups++
    Thread.sleep(50)
    return if (food == "oats") 389 else 304
}

// Impure: the number of eggs changes whenever someone cooks.
var fridgeEggs = 6
fun eggsIn(place: String): Int = if (place == "fridge") fridgeEggs else 0

fun main() {
    val kcal = memoize(::kcalPer100g)
    val foods = listOf("oats", "honey", "oats", "oats", "honey")
    val start = System.nanoTime()
    println(foods.map(kcal))
    println("lookups: $tableLookups for ${foods.size} calls, %d ms".format((System.nanoTime() - start) / 1_000_000))

    val eggs = memoize(::eggsIn)
    println("eggs in the fridge now:        ${eggs("fridge")}")
    fridgeEggs = 2                                        // someone makes an omelette
    println("eggs after someone's omelette: ${eggs("fridge")}   (really: ${eggsIn("fridge")})")
}
