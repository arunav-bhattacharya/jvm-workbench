package workbench.flows.l06

import kotlinx.coroutines.flow.Flow
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

/**
 * True for failures worth retrying: an IOException (the phone line dropped), or a
 * TimeoutCancellationException from timeout() or withTimeout (nobody answered in time).
 * Note that a timeout is a CancellationException, not an IOException.
 */
fun isTransient(e: Throwable): Boolean = TODO("IOException or TimeoutCancellationException")

/**
 * Retries this flow when it fails with an error that [retryOn] accepts, at most [maxRetries]
 * times. Before retry number k (counting from 0) it waits first * 2^k, capped at [max]:
 * 100, 200, 400 ms with the defaults. When the retries run out, or [retryOn] says no, the
 * ORIGINAL exception comes out, unchanged.
 *
 * A flow that always fails at once is therefore collected at 0, 100, 300 and 700 ms.
 */
fun <T> Flow<T>.retryWithBackoff(
    maxRetries: Long = 3,
    first: Duration = 100.milliseconds,
    max: Duration = 1.seconds,
    retryOn: (Throwable) -> Boolean = ::isTransient,
): Flow<T> = TODO("retryWhen { cause, attempt -> ... }")
