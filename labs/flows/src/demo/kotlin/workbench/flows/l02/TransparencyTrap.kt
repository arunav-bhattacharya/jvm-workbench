package workbench.flows.l02

import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.runBlocking

class LedgerException(message: String) : RuntimeException(message)

val batch = listOf("pay-1" to 4250L, "pay-2" to -990L, "pay-3" to 12000L)

/** The ledger refuses negative amounts. */
fun post(posted: MutableList<String>, id: String, cents: Long) {
    if (cents < 0) throw LedgerException("negative amount $cents for $id")
    posted += id
}

fun main() = runBlocking {
    println("=== flow { } with a try/catch around emit that logs and continues")
    val postings = flow {
        for ((id, cents) in batch) {
            try {
                emit(id to cents)
            } catch (e: Exception) {
                println("WARN posting $id failed, skipping it: ${e::class.simpleName}: ${e.message}")
            }
        }
    }
    val posted = mutableListOf<String>()
    postings.collect { (id, cents) -> post(posted, id, cents) }
    println("collect returned normally. posted=$posted")

    println()
    println("=== the same code on the toy flow from lesson 1")
    val toyPostings = toyFlow {
        for ((id, cents) in batch) {
            try {
                emit(id to cents)
            } catch (e: Exception) {
                println("WARN posting $id failed, skipping it: ${e::class.simpleName}: ${e.message}")
            }
        }
    }
    val toyPosted = mutableListOf<String>()
    toyPostings.collect { (id, cents) -> post(toyPosted, id, cents) }
    println("collect returned normally. posted=$toyPosted")

    println()
    println("=== emit from the catch block, without a try around it")
    try {
        flow {
            emit("pay-1" to 4250L)
            try { emit("pay-2" to -990L) } catch (e: LedgerException) { emit("pay-3" to 12000L) }
        }.collect { (id, cents) -> post(mutableListOf(), id, cents) }
    } catch (e: IllegalStateException) {
        println("collect threw IllegalStateException. cause=${e.cause} suppressed=${e.suppressed.toList()}")
        println(e.message)
    }
}
