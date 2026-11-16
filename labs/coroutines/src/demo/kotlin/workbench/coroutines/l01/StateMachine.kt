package workbench.coroutines.l01

import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking

suspend fun fryOnions(onions: String): String {
    delay(10) // pretend the onions take a while to turn golden
    return "golden $onions"
}

suspend fun simmer(base: String): String {
    delay(10) // pretend the pot takes a while
    return "sauce from $base"
}

/** Two suspension points, so the compiler builds a state machine with three states. */
suspend fun makeSauce(onions: String): String {
    val base = fryOnions(onions)   // suspension point 1
    val sauce = simmer(base)       // suspension point 2
    return sauce
}

fun main() = runBlocking {
    println(makeSauce("onions"))
}
