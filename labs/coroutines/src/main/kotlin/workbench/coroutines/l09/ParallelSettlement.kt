package workbench.coroutines.l09

/**
 * Settles every batch and returns batchId -> receipt.
 *
 * Use [workers] coroutines that take batch ids from one channel (fan-out), so at most
 * [workers] settle calls run at once and each batch is settled exactly once. Collect the
 * receipts from the workers through a second channel (fan-in). If any settle call throws,
 * settleInParallel throws it, and the other workers are cancelled.
 *
 * Bug: correct but sequential. Twelve batches of 100 ms take 1.2 s instead of 0.3 s with
 * four workers.
 */
suspend fun settleInParallel(
    batchIds: List<String>,
    workers: Int,
    settle: suspend (batchId: String) -> String,
): Map<String, String> =
    batchIds.associateWith { settle(it) }
