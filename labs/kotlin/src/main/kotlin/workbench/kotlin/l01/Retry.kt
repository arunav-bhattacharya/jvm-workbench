package workbench.kotlin.l01

import java.util.concurrent.CompletableFuture
import java.util.concurrent.Executor

/** Thrown when [retry] gives up. The last failure is the cause; the earlier ones are suppressed. */
class RetryExhaustedException(val attempts: Int, cause: Exception) :
    RuntimeException("gave up after $attempts attempt(s): ${cause.message}", cause)

/**
 * Builds the exception that [retry] throws when it gives up. It is finished: [retry] should call it.
 *
 * TODO 2: once retry calls this function, the compiler rejects the call. Read the error, then
 * fix it here, on this declaration. Keep it out of the Kotlin API (it is not meant for callers).
 */
private fun giveUp(attempts: Int, last: Exception, earlier: List<Exception>): RetryExhaustedException {
    val ex = RetryExhaustedException(attempts, last)
    earlier.forEach(ex::addSuppressed)
    return ex
}

/**
 * Runs [block] until it returns, at most [maxAttempts] times, and returns its result.
 * The block receives the attempt number, starting at 1.
 *
 * - A failure is an Exception thrown by the block. Errors (OutOfMemoryError and friends) are not caught.
 * - After a failure, go again only if attempts are left and shouldRetry(failure) is true.
 * - When you stop, throw giveUp(attempts made, the last failure, the earlier failures in order).
 * - maxAttempts below 1 is a caller bug: throw IllegalArgumentException before calling the block.
 *
 * TODO 1: write the loop. Keep the function inline and leave the `block` parameter as it is:
 * Callers.firstApproved puts a `return` inside the block, which only compiles while it is inlined.
 */
inline fun <T> retry(
    maxAttempts: Int,
    shouldRetry: (Exception) -> Boolean = { true },
    block: (attempt: Int) -> T,
): T = TODO("loop: return block(attempt), catch Exception, decide, throw giveUp(...) when you stop")

/**
 * Runs `retry(maxAttempts) { block(it) }` on [executor] and returns a future of the result.
 *
 * TODO 3: use CompletableFuture.supplyAsync({ ... }, executor). The compiler will stop you once.
 * Read the message, and add the modifier it asks for.
 */
inline fun <T> retryAsync(
    executor: Executor,
    maxAttempts: Int,
    block: (attempt: Int) -> T,
): CompletableFuture<T> = TODO("supplyAsync on the executor, with retry inside")
