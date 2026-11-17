package workbench.coroutines.l07

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext

private fun thread() = Thread.currentThread().name

fun main(args: Array<String>) = runBlocking {
    if (args.firstOrNull() == "wrong") {
        try {
            flow {
                withContext(Dispatchers.IO) { emit("flour,2000,g") } // emit from another context
            }.collect { println("collected $it") }
        } catch (e: IllegalStateException) {
            println("IllegalStateException: " + e.message!!.lines().first())
        }
        return@runBlocking
    }
    flow {
        for (line in listOf("flour,2000,g", "eggs,12,pcs")) {
            Thread.sleep(50) // a blocking read from the delivery note file
            println("read   on ${thread()}")
            emit(line)
        }
    }
        .map { println("parse  on ${thread()}"); parse(it) }
        .flowOn(Dispatchers.IO) // everything above this line runs on IO
        .map { println("format on ${thread()}"); "${it.first}: ${it.second}" }
        .collect { println("save   on ${thread()}  $it") }
}

private fun parse(line: String): Pair<String, Long> = line.split(",").let { it[0] to it[1].toLong() }
