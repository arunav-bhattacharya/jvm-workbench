package workbench.coroutines.l02

import kotlinx.coroutines.async
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

/** Predict the order of the lines before you run it. Everything runs on one thread. */
fun main() = runBlocking {
    println("A: before the builders")
    val audit = launch {
        println("C: audit starts")
        delay(100)
        println("F: audit written")
    }
    val price = async {
        println("D: price lookup starts")
        delay(50)
        1_084_512L
    }
    println("B: builders returned, audit.isActive=${audit.isActive}")
    println("E: price is ${price.await()}")
    audit.join()
    println("G: audit.isCompleted=${audit.isCompleted}")
}
