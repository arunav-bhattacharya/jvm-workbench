package workbench.coroutines.l01

import kotlinx.coroutines.delay
import kotlinx.coroutines.runBlocking

suspend fun tokenize(pan: String): String {
    delay(10) // pretend to call the vault
    return "tok_" + pan.takeLast(4)
}

suspend fun authorize(token: String): String {
    delay(10) // pretend to call the issuer
    return "approved:$token"
}

/** Two suspension points, so the compiler builds a state machine with three states. */
suspend fun chargeCard(pan: String): String {
    val token = tokenize(pan)   // suspension point 1
    val result = authorize(token) // suspension point 2
    return result
}

fun main() = runBlocking {
    println(chargeCard("4242424242424242"))
}
