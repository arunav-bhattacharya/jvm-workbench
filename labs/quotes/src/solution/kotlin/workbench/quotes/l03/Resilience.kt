package workbench.quotes.l03

import kotlinx.coroutines.async
import kotlinx.coroutines.cancelChildren
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.selects.select
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withTimeoutOrNull
import java.io.IOException
import kotlin.math.pow
import kotlin.random.Random
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds

/**
 * Up to [retries] more attempts after the first. The wait before retry n is [first] times 2^(n-1),
 * capped at [max], then moved by a random factor between 1 - [jitter] and 1 + [jitter].
 */
data class Backoff(
    val retries: Int = 2,
    val first: Duration = 50.milliseconds,
    val max: Duration = 200.milliseconds,
    val jitter: Double = 0.5,
) {
    fun nominal(n: Int): Duration = (first * 2.0.pow(n - 1)).coerceAtMost(max)
}

/**
 * Runs [call], and retries it after an IOException (a 503, a reset connection) with [backoff].
 * Any other exception, and the last IOException, goes to the caller. A cancel during a wait ends it.
 */
suspend fun <T> retrying(backoff: Backoff, random: Random, call: suspend () -> T): T {
    var n = 0
    while (true) {
        try {
            return call()
        } catch (e: IOException) {
            if (++n > backoff.retries) throw e                               // out of retries
            val factor = 1 + backoff.jitter * (random.nextDouble() * 2 - 1)  // 1 - jitter .. 1 + jitter
            delay(backoff.nominal(n) * factor)                               // so callers that failed together spread out
        }
    }
}

/**
 * Runs [call]. If it hasn't answered after [after], starts one more identical call and returns
 * whichever answers first. The other one is cancelled.
 */
suspend fun <T : Any> hedged(after: Duration, call: suspend () -> T): T = coroutineScope {
    val first = async { call() }
    val early = withTimeoutOrNull(after) { first.await() }                   // stops waiting, not the call
    if (early != null) return@coroutineScope early
    val second = async { call() }                                            // the hedge
    val winner = select { first.onAwait { it }; second.onAwait { it } }
    coroutineContext.cancelChildren()                                        // stop the loser
    winner
}

/**
 * A provider behind the three load rules: never more than [maxConcurrent] calls in flight to it;
 * and only if it is idempotent, retries with [backoff] and a hedge after [hedgeAfter] (null: no hedge).
 */
class GuardedProvider(
    private val delegate: Provider,
    maxConcurrent: Int,
    private val backoff: Backoff = Backoff(),
    private val hedgeAfter: Duration? = null,
    private val random: Random = Random.Default,
) : Provider {
    private val permits = Semaphore(maxConcurrent)

    override val name: String get() = delegate.name
    override val idempotent: Boolean get() = delegate.idempotent

    override suspend fun quote(symbol: String): Quote {
        val once: suspend () -> Quote = { permits.withPermit { delegate.quote(symbol) } }   // 1. every call holds a permit
        if (!delegate.idempotent) return once()                                            // 2. never repeat a firm quote
        val attempt: suspend () -> Quote = if (hedgeAfter == null) once else ({ hedged(hedgeAfter, once) })
        return retrying(backoff, random, attempt)                                          // 3. a hedge per attempt
    }
}
