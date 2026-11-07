package workbench.quotes.l02

import kotlinx.coroutines.delay
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import kotlin.coroutines.cancellation.CancellationException
import kotlin.time.Duration

/**
 * An in-process provider the test controls: it answers [price] after [latency], or throws
 * [failure] after [latency]. Every cancelled call adds its name to [cancelled].
 */
class FakeProvider(
    override val name: String,
    private val price: String,
    private val latency: Duration,
    private val failure: Exception? = null,
    private val cancelled: MutableList<String> = CopyOnWriteArrayList(),
) : Provider {
    val calls = AtomicInteger()

    override suspend fun quote(symbol: String): Quote {
        calls.incrementAndGet()
        try {
            delay(latency)
        } catch (e: CancellationException) {
            cancelled += name
            throw e
        }
        failure?.let { throw it }
        return Quote.live(symbol, price, name)
    }
}
