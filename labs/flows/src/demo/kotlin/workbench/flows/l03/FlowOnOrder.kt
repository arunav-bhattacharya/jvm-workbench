package workbench.flows.l03

import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.runBlocking
import java.util.concurrent.Executors

val lines = listOf("pay-1,4250,EUR", "pay-2,990,EUR", "pay-3,12000,GBP")

/** The settlement reader from lesson 1. Each line is read instantly; it prints which thread read it. */
fun settlementIds(): Flow<String> = flow {
    for (line in lines) {
        val id = line.substringBefore(",")
        println("read    $id   on ${Thread.currentThread().name}")
        emit(id)
    }
}

fun main() = runBlocking {
    val io = Executors.newSingleThreadExecutor { r -> Thread(r, "io-thread") }.asCoroutineDispatcher()

    println("=== plain, as in lesson 1")
    settlementIds().collect { id ->
        delay(30)                                   // the ledger write
        println("posted  $id   on ${Thread.currentThread().name}")
    }

    println("=== with .flowOn(io)")
    settlementIds().flowOn(io).collect { id ->
        delay(30)
        println("posted  $id   on ${Thread.currentThread().name}")
    }
    io.close()
}
