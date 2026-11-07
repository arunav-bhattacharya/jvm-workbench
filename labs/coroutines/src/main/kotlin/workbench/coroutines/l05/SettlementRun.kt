package workbench.coroutines.l05

/**
 * Settles each batch in turn. A batch that fails is logged and skipped, so one bad batch
 * doesn't stop the run. Returns the ids of the batches that failed.
 *
 * Bug: when the caller is cancelled (the pod is shutting down), the run doesn't stop.
 * runCatching also catches the CancellationException, so the batch in progress is
 * reported as "failed", and every remaining batch is started and "fails" at once.
 * Make cancellation end the run, while ordinary failures are still logged and skipped.
 */
suspend fun settleEach(batchIds: List<String>, settle: suspend (batchId: String) -> Unit): List<String> {
    val failed = mutableListOf<String>()
    for (id in batchIds) {
        runCatching { settle(id) }
            .onFailure { e ->
                println("batch $id failed, skipping: $e")
                failed += id
            }
    }
    return failed
}
