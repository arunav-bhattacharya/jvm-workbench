package workbench.functional.l07

/**
 * Runs [block] and wraps what it returns or throws in a Result, like runCatching, with one difference:
 * a CancellationException is never captured. It must propagate, so a cancelled coroutine stops instead
 * of carrying on with a "failed" Result in its hand.
 *
 * This version is plain runCatching, so it swallows cancellation. Fix it.
 */
suspend fun <T> runCatchingCancellable(block: suspend () -> T): Result<T> =
    runCatching { block() }
