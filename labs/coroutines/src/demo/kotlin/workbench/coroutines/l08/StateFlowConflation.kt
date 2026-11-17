package workbench.coroutines.l08

import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking

data class Menu(val soup: String)

fun main() = runBlocking {
    val board = MutableStateFlow(Menu("tomato"))
    val hall = launch(start = CoroutineStart.UNDISPATCHED) {
        board.collect { menu ->
            println("the board in the hall shows ${menu.soup} soup")
            delay(100) // chalking up the board is slow
        }
    }
    // the cook changes her mind three times while the board is being chalked up
    board.value = Menu("leek")
    board.value = Menu("pea")
    board.value = Menu("onion")
    delay(150)
    println("setting an equal menu again (a new object, same fields)")
    board.value = Menu("onion")
    delay(150)
    println("value is ${board.value.soup}; the collector is still waiting, because a StateFlow never completes")
    hall.cancel()
}
