package workbench.coroutines.l05

import kotlin.coroutines.cancellation.CancellationException

suspend fun settleEach(batchIds: List<String>, settle: suspend (batchId: String) -> Unit): List<String> {
    val failed = mutableListOf<String>()
    for (id in batchIds) {
        runCatching { settle(id) }
            .onFailure { e ->
                // runCatching catches every Throwable, CancellationException included.
                // Rethrow it: it is the coroutine being cancelled, not the batch failing.
                if (e is CancellationException) throw e
                println("batch $id failed, skipping: $e")
                failed += id
            }
    }
    return failed
}
