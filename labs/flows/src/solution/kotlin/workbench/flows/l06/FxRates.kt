package workbench.flows.l06

import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.catch
import kotlinx.coroutines.flow.emitAll
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.timeout
import kotlin.time.Duration.Companion.milliseconds

@OptIn(FlowPreview::class) // timeout() is a preview API in 1.11.0
fun fxRate(pair: String, primary: RateProvider, fallback: RateProvider): Flow<Rate> =
    primary.rate(pair)
        .timeout(300.milliseconds)        // 1. per attempt: above retryWhen, so each call gets its own 300 ms
        .retryWithBackoff()               // 2. retries IOException and TimeoutCancellationException
        .catch { e ->                     // 3. reached once retries are used up, or for a non-transient error
            if (!isTransient(e)) throw e  // 4. a bad pair or a bug is the caller's problem
            emitAll(fallback.rate(pair))
        }
// 5. needs no code: catch and retryWhen both let the caller's own cancellation pass through.

fun uniquePayments(feed: Flow<Payment>): Flow<Payment> = flow {
    val seen = HashSet<String>()           // one set per collection, so the flow stays cold and re-runnable
    feed.retryWithBackoff().collect { payment ->
        if (seen.add(payment.id)) emit(payment)   // a retry replays the feed from the top: skip what we've sent
    }
}
