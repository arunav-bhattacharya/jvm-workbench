package workbench.flows.l03

import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.runBlocking
import java.util.concurrent.Executors

val deliveryNote = listOf("flour,2000,g", "eggs,12,pcs", "milk,1000,ml")

/** Reads the grocer's delivery note. Each line is read at once; it prints which thread read it. */
fun deliveryItems(): Flow<String> = flow {
    for (line in deliveryNote) {
        val item = line.substringBefore(",")
        println("read    $item   on ${Thread.currentThread().name}")
        emit(item)
    }
}

fun main() = runBlocking {
    val io = Executors.newSingleThreadExecutor { r -> Thread(r, "io-thread") }.asCoroutineDispatcher()

    println("=== plain, as in lesson 1")
    deliveryItems().collect { item ->
        delay(30)                                   // put it away and write it in the pantry book
        println("stored  $item   on ${Thread.currentThread().name}")
    }

    println("=== with .flowOn(io)")
    deliveryItems().flowOn(io).collect { item ->
        delay(30)
        println("stored  $item   on ${Thread.currentThread().name}")
    }
    io.close()
}
