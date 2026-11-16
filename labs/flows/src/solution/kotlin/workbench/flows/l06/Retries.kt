package workbench.flows.l06

import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.retryWhen
import java.io.IOException
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

// A timeout is a CancellationException, not an IOException, so it has to be listed on its own.
fun isTransient(e: Throwable): Boolean = e is IOException || e is TimeoutCancellationException

fun <T> Flow<T>.retryWithBackoff(
    maxRetries: Long = 3,
    first: Duration = 100.milliseconds,
    max: Duration = 1.seconds,
    retryOn: (Throwable) -> Boolean = ::isTransient,
): Flow<T> = retryWhen { cause, attempt ->                     // attempt is 0 on the first failure
    if (attempt >= maxRetries || !retryOn(cause)) return@retryWhen false   // false: the original cause comes out
    delay(minOf(first * (1L shl attempt.toInt()).toDouble(), max))       // 100, 200, 400 ms ... capped
    true                                                                   // true: collect the upstream again
}
