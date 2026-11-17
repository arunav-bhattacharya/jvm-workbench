package workbench.coroutines.l07

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking

private val pages = listOf(listOf("apples", "bananas"), listOf("cherries", "dates"), listOf("figs", "grapes"))

/** Three pages of two items each, from the grocer's shop, which takes 20 ms per page. */
fun aisle(name: String): Flow<String> = flow {
    for ((page, items) in pages.withIndex()) {
        println("  fetching page $page of the $name aisle")
        delay(20)
        for (item in items) emit(item)
    }
}

fun main() = runBlocking {
    println("building the flow")
    val fruit = aisle("fruit")
    println("built; nothing fetched yet")

    println("first collect:")
    println("  got ${fruit.toList()}")

    println("second collect:")
    println("  got ${fruit.toList()}")

    println("take(3):")
    println("  got ${fruit.take(3).toList()}")
}
