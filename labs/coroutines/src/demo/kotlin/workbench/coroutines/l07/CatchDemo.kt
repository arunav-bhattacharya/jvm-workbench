package workbench.coroutines.l07

import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.runBlocking
import java.io.IOException

fun main(args: Array<String>) = runBlocking {
    val failIn = args.firstOrNull() ?: "upstream" // or "collector"
    val lines = flow {
        emit("flour,2000,g")
        emit("eggs,12,pcs")
        if (failIn == "upstream") throw IOException("delivery note torn")
        emit("butter,250,g")
    }
    try {
        lines
            .map { it.substringBefore(",") }
            .onCompletion { cause -> println("onCompletion: cause = $cause") }
            .catch { e -> println("catch: $e"); emit("ABORTED") }
            .collect { item ->
                println("collect $item")
                if (failIn == "collector" && item == "eggs") throw IllegalStateException("pantry shelf full")
            }
        println("collect returned normally")
    } catch (e: Exception) {
        println("the caller got: $e")
    }
}
