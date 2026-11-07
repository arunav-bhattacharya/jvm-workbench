package workbench.coroutines.l07

import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.runBlocking

/** Three pages of two entries each, from a ledger API that takes 20 ms per page. */
fun entries(accountId: String): Flow<String> = flow {
    for (page in 0 until 3) {
        println("  fetching page $page of $accountId")
        delay(20)
        emit("e${page * 2 + 1}")
        emit("e${page * 2 + 2}")
    }
}

fun main() = runBlocking {
    println("building the flow")
    val flow = entries("acc-1")
    println("built; nothing fetched yet")

    println("first collect:")
    println("  got ${flow.toList()}")

    println("second collect:")
    println("  got ${flow.toList()}")

    println("take(3):")
    println("  got ${flow.take(3).toList()}")
}
