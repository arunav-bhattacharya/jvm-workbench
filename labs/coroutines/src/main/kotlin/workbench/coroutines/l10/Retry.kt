package workbench.coroutines.l10

import java.io.IOException
import kotlin.time.Duration

/**
 * Calls [block] up to [times] times. [block] receives the attempt number, starting at 1.
 *
 * - If an attempt throws an exception for which [retryOn] is true, wait and try again. The
 *   first wait is [initialDelay]; each later wait is the previous one times [factor], but never
 *   more than [maxDelay].
 * - If the last attempt fails, rethrow its exception. If [retryOn] is false, rethrow at once.
 * - Never retry a CancellationException: cancellation must stop the retries, even mid-wait.
 *
 * Example: times = 4, initialDelay = 100 ms, factor = 2 waits 100, 200 and 400 ms.
 */
suspend fun <T> retryWithBackoff(
    times: Int,
    initialDelay: Duration,
    maxDelay: Duration,
    factor: Double = 2.0,
    retryOn: (Throwable) -> Boolean = { it is IOException },
    block: suspend (attempt: Int) -> T,
): T {
    TODO("loop over the attempts with try/catch, delay between them, and grow the delay")
}
