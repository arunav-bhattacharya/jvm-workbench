package workbench.coroutines.l09

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger

@OptIn(ExperimentalCoroutinesApi::class)
class ChannelsTest {

    // ---- settleInParallel: fan-out / fan-in ----

    @Test
    fun `four workers settle twelve batches in three rounds`() = runTest {
        val active = AtomicInteger()
        val peak = AtomicInteger()
        val ids = (1..12).map { "batch-$it" }
        val receipts = settleInParallel(ids, workers = 4) { id ->
            peak.accumulateAndGet(active.incrementAndGet(), ::maxOf)
            delay(100) // the acquirer call
            active.decrementAndGet()
            "rcpt-$id"
        }
        assertThat(receipts).isEqualTo(ids.associateWith { "rcpt-$it" })
        assertThat(peak.get()).`as`("settle calls running at once").isEqualTo(4)
        assertThat(currentTime).`as`("virtual ms: 12 batches / 4 workers x 100 ms").isEqualTo(300)
    }

    @Test
    fun `every batch is settled exactly once`() = runTest {
        val calls = ConcurrentHashMap<String, AtomicInteger>()
        val ids = (1..50).map { "batch-$it" }
        settleInParallel(ids, workers = 7) { id ->
            calls.computeIfAbsent(id) { AtomicInteger() }.incrementAndGet()
            delay((id.removePrefix("batch-").toLong() % 5) * 10)
            id
        }
        assertThat(calls.keys).containsExactlyInAnyOrderElementsOf(ids)
        assertThat(calls.values.map { it.get() }).containsOnly(1)
    }

    @Test
    fun `a failing batch fails the call and cancels the other workers`() = runTest {
        val finished = CopyOnWriteArrayList<String>()
        val thrown = runCatching {
            settleInParallel((1..8).map { "batch-$it" }, workers = 4) { id ->
                if (id == "batch-2") { delay(50); throw IOException("acquirer rejected batch-2") }
                delay(1_000)
                finished += id
                id
            }
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IOException::class.java).hasMessage("acquirer rejected batch-2")
        assertThat(finished).`as`("batches that finished after the failure").isEmpty()
        assertThat(currentTime).isEqualTo(50)
    }

    // ---- events(): callbackFlow ----

    private class FakeBus : PaymentEventBus {
        val listeners = CopyOnWriteArrayList<(PaymentEvent) -> Unit>()
        val unregistered = AtomicInteger()
        override fun register(listener: (PaymentEvent) -> Unit): Registration {
            listeners += listener
            return Registration { listeners -= listener; unregistered.incrementAndGet() }
        }
        fun publish(e: PaymentEvent) = listeners.forEach { it(e) }
    }

    @Test
    fun `events delivers what the bus publishes, then unregisters when the collector stops`() = runTest {
        val bus = FakeBus()
        val received = CopyOnWriteArrayList<PaymentEvent>()
        val collector = backgroundScope.launch { bus.events().take(2).toList(received) }
        runCurrent()
        assertThat(bus.listeners).`as`("listeners registered once collecting").hasSize(1)

        bus.publish(PaymentEvent("pay-1", "AUTHORIZED"))
        bus.publish(PaymentEvent("pay-1", "CAPTURED"))
        runCurrent()

        assertThat(received).containsExactly(PaymentEvent("pay-1", "AUTHORIZED"), PaymentEvent("pay-1", "CAPTURED"))
        assertThat(collector.isCompleted).isTrue()
        assertThat(bus.unregistered.get()).`as`("unregister calls").isEqualTo(1)
        assertThat(bus.listeners).isEmpty()
    }

    @Test
    fun `cancelling the collector unregisters the listener`() = runTest {
        val bus = FakeBus()
        val collector = backgroundScope.launch { bus.events().collect { } }
        runCurrent()
        assertThat(bus.listeners).hasSize(1)
        collector.cancel()
        runCurrent()
        assertThat(bus.unregistered.get()).isEqualTo(1)
    }

    // ---- fastestQuote: select ----

    private fun acquirer(name: String, ms: Long, fee: Int, cancelled: MutableList<String>): suspend () -> Quote = {
        try { delay(ms); Quote(name, fee) } catch (e: kotlin.coroutines.cancellation.CancellationException) { cancelled += name; throw e }
    }

    @Test
    fun `fastestQuote returns the first quote to arrive and cancels the others`() = runTest {
        val cancelled = CopyOnWriteArrayList<String>()
        val quote = fastestQuote(listOf(
            acquirer("north", 300, 180, cancelled),
            acquirer("east", 120, 210, cancelled),
            acquirer("west", 200, 150, cancelled),
        ))
        assertThat(quote).isEqualTo(Quote("east", 210))
        assertThat(currentTime).`as`("virtual ms").isEqualTo(120)
        assertThat(cancelled).containsExactlyInAnyOrder("north", "west")
    }

    @Test
    fun `fastestQuote fails when the first to answer fails`() = runTest {
        val cancelled = CopyOnWriteArrayList<String>()
        val thrown = runCatching {
            fastestQuote(listOf(
                acquirer("north", 300, 180, cancelled),
                { delay(80); throw IOException("east is down") },
            ))
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IOException::class.java).hasMessage("east is down")
        assertThat(currentTime).isEqualTo(80)
        assertThat(cancelled).containsExactly("north")
    }
}
