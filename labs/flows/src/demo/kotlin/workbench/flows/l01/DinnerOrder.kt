package workbench.flows.l01

import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.runBlocking

/** A cook serves three dishes to one diner through a flow. Write down the order of the lines before you run it. */
fun main() = runBlocking {
    val card = listOf("soup", "salad", "roast")         // the recipe card: three dishes, in order

    val dinner = flow {
        for (dish in card) {
            println("cook    $dish")
            emit(dish)
            println("emit($dish) returned")
        }
    }
    println("flow built")

    dinner.collect { dish -> println("eat     $dish") }
    println("collect returned")
}
