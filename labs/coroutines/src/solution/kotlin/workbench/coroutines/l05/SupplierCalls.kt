package workbench.coroutines.l05

import kotlin.coroutines.cancellation.CancellationException

suspend fun confirmEach(orders: List<String>, confirm: suspend (order: String) -> Unit): List<String> {
    val failed = mutableListOf<String>()
    for (order in orders) {
        runCatching { confirm(order) }
            .onFailure { e ->
                // runCatching catches every Throwable, CancellationException included.
                // Rethrow it: it is the coroutine being cancelled, not the call failing.
                if (e is CancellationException) throw e
                println("call for $order failed, skipping: $e")
                failed += order
            }
    }
    return failed
}
