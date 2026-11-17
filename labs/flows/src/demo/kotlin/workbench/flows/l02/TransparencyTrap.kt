package workbench.flows.l02

import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.runBlocking

class SentBackException(message: String) : RuntimeException(message)

val dinner = listOf("soup", "salad", "roast")

/** The diner sends back anything too salty. Tonight that is the salad. */
fun eat(eaten: MutableList<String>, dish: String) {
    if (dish == "salad") throw SentBackException("too salty: $dish")
    eaten += dish
}

fun main() = runBlocking {
    println("=== flow { } with a try/catch around emit that says sorry and carries on")
    val plates = flow {
        for (dish in dinner) {
            try {
                emit(dish)
            } catch (e: Exception) {
                println("SORRY $dish came back, serving the next dish. ${e::class.simpleName}: ${e.message}")
            }
        }
    }
    val eaten = mutableListOf<String>()
    plates.collect { dish -> eat(eaten, dish) }
    println("collect returned normally. eaten=$eaten")

    println()
    println("=== the same code on the toy flow from lesson 1")
    val toyPlates = toyFlow {
        for (dish in dinner) {
            try {
                emit(dish)
            } catch (e: Exception) {
                println("SORRY $dish came back, serving the next dish. ${e::class.simpleName}: ${e.message}")
            }
        }
    }
    val toyEaten = mutableListOf<String>()
    toyPlates.collect { dish -> eat(toyEaten, dish) }
    println("collect returned normally. eaten=$toyEaten")

    println()
    println("=== emit from the catch block, without a try around it")
    try {
        flow {
            emit("soup")
            try { emit("salad") } catch (e: SentBackException) { emit("roast") }
        }.collect { dish -> eat(mutableListOf(), dish) }
    } catch (e: IllegalStateException) {
        println("collect threw IllegalStateException. cause=${e.cause} suppressed=${e.suppressed.toList()}")
        println(e.message)
    }
}
