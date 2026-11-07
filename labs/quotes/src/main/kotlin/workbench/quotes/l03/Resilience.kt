package workbench.quotes.l03

import kotlinx.coroutines.delay
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
 *
 * This version waits exactly `nominal(n)`, so a thousand clients that failed together retry in the
 * same millisecond. Add the jitter: multiply the wait by `1 + jitter * r`, where `r` is
 * `random.nextDouble() * 2 - 1` (between -1 and 1).
 */
suspend fun <T> retrying(backoff: Backoff, random: Random, call: suspend () -> T): T {
    var n = 0
    while (true) {
        try {
            return call()
        } catch (e: IOException) {
            if (++n > backoff.retries) throw e                               // out of retries
            delay(backoff.nominal(n))                                        // TODO: jitter
        }
    }
}

/**
 * Runs [call]. If it hasn't answered after [after], starts one more identical call and returns
 * whichever answers first. The other one is cancelled.
 *
 * Inside `coroutineScope`: start the first call with `async`; wait for it with
 * `withTimeoutOrNull(after) { first.await() }` (that stops the waiting, not the call); if that gave
 * null, start the second with `async`, `select` on both `onAwait` clauses, then
 * `coroutineContext.cancelChildren()` to stop the loser.
 */
suspend fun <T : Any> hedged(after: Duration, call: suspend () -> T): T {
    TODO("first call, wait up to `after`, then a hedge and a select")
}

/**
 * A provider behind the three load rules: never more than [maxConcurrent] calls in flight to it;
 * and only if it is idempotent, retries with [backoff] and a hedge after [hedgeAfter] (null: no hedge).
 *
 * 1. Give the class a `Semaphore(maxConcurrent)` (kotlinx.coroutines.sync), and make every single
 *    call to [delegate] hold a permit: `permits.withPermit { delegate.quote(symbol) }`. A hedge is a
 *    second call, so it needs a permit of its own.
 * 2. If the delegate is not idempotent, make that one call and nothing else.
 * 3. Otherwise retry the call with [retrying]; if [hedgeAfter] is set, each attempt is
 *    `hedged(hedgeAfter) { ...the permitted call... }`.
 */
class GuardedProvider(
    private val delegate: Provider,
    maxConcurrent: Int,
    private val backoff: Backoff = Backoff(),
    private val hedgeAfter: Duration? = null,
    private val random: Random = Random.Default,
) : Provider {
    override val name: String get() = delegate.name
    override val idempotent: Boolean get() = delegate.idempotent

    override suspend fun quote(symbol: String): Quote = TODO("bulkhead, then retry and hedge for idempotent providers")
}
