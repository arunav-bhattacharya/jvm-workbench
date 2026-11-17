package workbench.coroutines.l11

import java.util.concurrent.CompletableFuture

// Shared model. This file is the same in src/main and src/solution.

/** What the neighbour's Java code asks our kitchen to cook. */
data class Order(val dish: String, val portions: Int)

enum class Outcome { SERVED, REFUSED }

/** The bakery's Java library: returns at once with a future that completes with the loaves left. */
fun interface JavaBakery {
    fun loavesLeft(bread: String): CompletableFuture<Int>
}

data class Recipe(val dish: String, val minutes: Int)

/** A Kotlin recipe book. Returns null when it has no recipe for the dish. */
fun interface RecipeBook {
    suspend fun recipe(dish: String): Recipe?
}
