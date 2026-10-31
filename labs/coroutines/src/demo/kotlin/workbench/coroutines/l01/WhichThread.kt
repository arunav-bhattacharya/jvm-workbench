package workbench.coroutines.l01

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

private fun where() = Thread.currentThread().name.removePrefix("DefaultDispatcher-")

/** A suspend function that never suspends runs on its caller's thread, start to finish. */
suspend fun checksum(digits: String): Int {
    var sum = 0
    for (c in digits) sum = (sum * 31 + c.code) % 1_000_003
    return sum // no suspension point anywhere: plain code with a suspend label on it
}

fun main() = runBlocking {
    println("main coroutine runs on ${where()}")
    println("checksum ${checksum("4242424242424242")} computed on ${where()}")

    repeat(4) { id ->
        launch(Dispatchers.Default) {
            val seen = mutableListOf<String>()
            repeat(4) {
                seen += where()
                delay(20) // suspends; any free Default thread may resume it
            }
            println("payment $id ran on ${seen.joinToString(" -> ")}")
        }
    }
}
