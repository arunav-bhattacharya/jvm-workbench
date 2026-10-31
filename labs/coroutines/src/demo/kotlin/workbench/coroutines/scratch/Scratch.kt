package workbench.coroutines.scratch

import kotlinx.coroutines.*

fun main() = runBlocking {
    val r = withTimeoutOrNull(500) {
        coroutineScope {
            val lazy = async(start = CoroutineStart.LAZY) { 42 }
            println("lazy isActive=${lazy.isActive}")
            "body done"
        }
    }
    println("scope result: $r")
}
