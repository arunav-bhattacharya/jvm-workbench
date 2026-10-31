package workbench.coroutines.l03

import kotlinx.coroutines.DelicateCoroutinesApi
import kotlinx.coroutines.GlobalScope
import kotlinx.coroutines.launch

/**
 * Settles every batch at the same time.
 *
 * Required behavior:
 * - returns only after every batch has been settled;
 * - if one batch fails, the others are cancelled and the failure is thrown to the caller;
 * - if the caller is cancelled, every batch is cancelled.
 *
 * This version leaks: it starts the work in GlobalScope and returns at once. Fix it.
 */
@OptIn(DelicateCoroutinesApi::class)
suspend fun settleAll(batchIds: List<String>, settle: suspend (String) -> Unit) {
    for (id in batchIds) {
        GlobalScope.launch { settle(id) }
    }
}
