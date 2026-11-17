package workbench.coroutines.l01

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

private fun where() = Thread.currentThread().name.removePrefix("DefaultDispatcher-")

/** A suspend function that never suspends runs on its caller's thread, start to finish. */
suspend fun scaleRecipe(gramsForFour: List<Int>, guests: Int): Int {
    var total = 0
    for (g in gramsForFour) total += g * guests / 4
    return total // no suspension point anywhere: plain code with a suspend label on it
}

fun main() = runBlocking {
    println("main coroutine runs on ${where()}")
    println("scaleRecipe says ${scaleRecipe(listOf(400, 250, 120, 30), 10)} g, computed on ${where()}")

    repeat(4) { id ->
        launch(Dispatchers.Default) {
            val seen = mutableListOf<String>()
            repeat(4) {
                seen += where()
                delay(20) // suspends; any free Default thread may resume it
            }
            println("dish $id ran on ${seen.joinToString(" -> ")}")
        }
    }
}
