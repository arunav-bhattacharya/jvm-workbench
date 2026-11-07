package workbench.coroutines.l10

import kotlinx.coroutines.delay
import java.io.IOException
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration

suspend fun <T> retryWithBackoff(
    times: Int,
    initialDelay: Duration,
    maxDelay: Duration,
    factor: Double = 2.0,
    retryOn: (Throwable) -> Boolean = { it is IOException },
    block: suspend (attempt: Int) -> T,
): T {
    require(times >= 1) { "times must be at least 1" }
    var wait = initialDelay
    for (attempt in 1 until times) {
        try {
            return block(attempt)
        } catch (e: CancellationException) {
            throw e // 1. a cancel is not a failed attempt
        } catch (e: Exception) {
            if (!retryOn(e)) throw e // 2. not worth retrying
        }
        delay(wait) // 3. cancellable: a cancel during the wait ends the retries
        wait = (wait * factor).coerceAtMost(maxDelay)
    }
    return block(times) // 4. the last attempt: whatever it throws reaches the caller
}
