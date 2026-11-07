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
        emit("pay-1,4250,EUR")
        emit("pay-2,-990,EUR")
        if (failIn == "upstream") throw IOException("settlement file truncated")
        emit("pay-3,120000,GBP")
    }
    try {
        lines
            .map { it.substringBefore(",") }
            .onCompletion { cause -> println("onCompletion: cause = $cause") }
            .catch { e -> println("catch: $e"); emit("ABORTED") }
            .collect { id ->
                println("collect $id")
                if (failIn == "collector" && id == "pay-2") throw IllegalStateException("ledger db down")
            }
        println("collect returned normally")
    } catch (e: Exception) {
        println("the caller got: $e")
    }
}
