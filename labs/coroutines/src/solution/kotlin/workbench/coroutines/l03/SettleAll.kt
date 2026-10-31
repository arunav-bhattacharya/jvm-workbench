package workbench.coroutines.l03

import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch

suspend fun settleAll(batchIds: List<String>, settle: suspend (String) -> Unit) = coroutineScope {
    // every launch is a child of this scope: the scope waits for all of them,
    // cancels the rest if one fails, and is cancelled itself if the caller is
    for (id in batchIds) {
        launch { settle(id) }
    }
}
