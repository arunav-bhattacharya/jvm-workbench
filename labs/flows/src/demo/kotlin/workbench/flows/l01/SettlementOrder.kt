package workbench.flows.l01

import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.runBlocking

/** A settlement-file reader feeds a ledger writer. Write down the order of the lines before you run it. */
fun main() = runBlocking {
    val lines = listOf("pay-1,4250,EUR", "pay-2,990,EUR", "pay-3,12000,GBP")

    val records = flow {
        for (line in lines) {
            val id = line.substringBefore(",")
            println("read    $id")
            emit(id)
            println("emit($id) returned")
        }
    }
    println("flow built")

    records.collect { id -> println("posted  $id") }
    println("collect returned")
}
