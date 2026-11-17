package workbench.coroutines.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** Predict the order of the lines before you run it. Everything runs on one thread. */
fun main() = runBlocking {
    println("A: before the builders")
    val table = launch {
        println("C: table: start setting it")
        delay(100)
        println("F: table: set")
    }
    val oven = async {
        println("D: oven: checking the temperature")
        delay(50)
        180
    }
    println("B: builders returned, table.isActive=${table.isActive}")
    println("E: oven is at ${oven.await()} degrees")
    table.join()
    println("G: table.isCompleted=${table.isCompleted}")
}
