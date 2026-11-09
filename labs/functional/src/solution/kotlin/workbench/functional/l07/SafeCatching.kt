package workbench.functional.l07

import kotlin.coroutines.cancellation.CancellationException

suspend fun <T> runCatchingCancellable(block: suspend () -> T): Result<T> =
    try {
        Result.success(block())
    } catch (e: CancellationException) {
        throw e                                // the cancel must keep travelling up the stack
    } catch (e: Throwable) {
        Result.failure(e)
    }
// Shorter, same behaviour: runCatching { block() }.onFailure { if (it is CancellationException) throw it }
