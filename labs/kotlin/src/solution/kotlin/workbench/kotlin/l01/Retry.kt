package workbench.kotlin.l01

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executor

/** Thrown when [retry] gives up. The last failure is the cause; the earlier ones are suppressed. */
class RetryExhaustedException(val attempts: Int, cause: Exception) :
    RuntimeException("gave up after $attempts attempt(s): ${cause.message}", cause)

/**
 * Builds the exception that [retry] throws when it gives up.
 *
 * A public inline function is pasted into callers in other modules, so its body may only touch
 * what those callers could touch. `private` would not compile. `@PublishedApi internal` keeps
 * this function out of the Kotlin API but makes it public in the bytecode, so inlined copies can call it.
 */
@PublishedApi
internal fun giveUp(attempts: Int, last: Exception, earlier: List<Exception>): RetryExhaustedException {
    val ex = RetryExhaustedException(attempts, last)
    earlier.forEach(ex::addSuppressed)
    return ex
}

/**
 * Runs [block] until it returns, at most [maxAttempts] times, and returns its result.
 * The block receives the attempt number, starting at 1.
 */
inline fun <T> retry(
    maxAttempts: Int,
    shouldRetry: (Exception) -> Boolean = { true },
    block: (attempt: Int) -> T,
): T {
    require(maxAttempts >= 1) { "maxAttempts must be at least 1, was $maxAttempts" }
    val earlier = ArrayList<Exception>()
    var attempt = 1
    while (true) {
        try {
            // 1. block is pasted in here, so a bare `return` inside it leaves the caller
            return block(attempt)
        } catch (e: Exception) {
            // 2. out of attempts, or a failure that retrying won't fix: report and stop
            if (attempt == maxAttempts || !shouldRetry(e)) throw giveUp(attempt, e, earlier)
            // 3. keep the failure for the report and go round again
            earlier += e
        }
        attempt++
    }
}

/**
 * Runs `retry(maxAttempts, block = block)` on [executor] and returns a future of the result.
 *
 * The block now runs inside a Supplier, on another thread. A `return` in it could not leave the
 * caller, which may have finished long ago. `crossinline` tells the compiler to forbid such returns,
 * and the block can then be inlined into the Supplier the compiler generates.
 */
inline fun <T> retryAsync(
    executor: Executor,
    maxAttempts: Int,
    crossinline block: (attempt: Int) -> T,
): CompletableFuture<T> =
    CompletableFuture.supplyAsync({ retry(maxAttempts) { block(it) } }, executor)
