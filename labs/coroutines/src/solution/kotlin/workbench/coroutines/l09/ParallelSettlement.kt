package workbench.coroutines.l09

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.channels.produce
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.joinAll
import kotlinx.coroutines.launch

@OptIn(ExperimentalCoroutinesApi::class) // produce is still marked experimental
suspend fun settleInParallel(
    batchIds: List<String>,
    workers: Int,
    settle: suspend (batchId: String) -> String,
): Map<String, String> = coroutineScope {
    // 1. fan-out source: a rendezvous channel, closed automatically when the block ends
    val ids = produce { for (id in batchIds) send(id) }
    // 2. fan-in: every worker sends its receipts here
    val receipts = Channel<Pair<String, String>>()
    val pool = List(workers) {
        launch {
            for (id in ids) receipts.send(id to settle(id)) // each id is received by exactly one worker
        }
    }
    // 3. close the fan-in channel once every worker is done, so the loop below can end
    launch { pool.joinAll(); receipts.close() }
    val result = LinkedHashMap<String, String>()
    for ((id, receipt) in receipts) result[id] = receipt
    result
}
