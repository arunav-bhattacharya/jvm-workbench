package workbench.quotes.l03

import kotlinx.coroutines.delay
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration
import kotlin.time.Duration.Companion.milliseconds

/**
 * An in-process provider the test controls. [script] says, for call number n (from 1), how long the
 * call takes and what it throws at the end (null: it answers [price]). It counts calls, the most
 * calls in flight at once ([peak]), when each call started ([started], from [clock]) and which
 * calls were cancelled.
 */
class FakeProvider(
    override val name: String,
    override val idempotent: Boolean = true,
    private val price: String = "1.0842",
    private val clock: () -> Long = { 0L },
    val cancelled: MutableList<String> = CopyOnWriteArrayList(),
    private val script: (call: Int) -> Pair<Duration, Exception?> = { 100.milliseconds to null },
) : Provider {
    val calls = AtomicInteger()
    val peak = AtomicInteger()
    val started: MutableList<Long> = CopyOnWriteArrayList()
    val cancelledCalls: MutableList<Int> = CopyOnWriteArrayList()
    private val active = AtomicInteger()

    override suspend fun quote(symbol: String): Quote {
        val n = calls.incrementAndGet()
        started += clock()
        peak.accumulateAndGet(active.incrementAndGet(), ::maxOf)
        try {
            val (latency, failure) = script(n)
            delay(latency)
            failure?.let { throw it }
            return Quote.live(symbol, price, name)
        } catch (e: CancellationException) {
            cancelled += name
            cancelledCalls += n
            throw e
        } finally {
            active.decrementAndGet()
        }
    }
}
