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

    // ---- cookAll: fan-out / fan-in ----

    @Test
    fun `four helpers cook twelve dishes in three rounds`() = runTest {
        val active = AtomicInteger()
        val peak = AtomicInteger()
        val dishes = (1..12).map { "dish-$it" }
        val plates = cookAll(dishes, helpers = 4) { dish ->
            peak.accumulateAndGet(active.incrementAndGet(), ::maxOf)
            delay(100) // cooking
            active.decrementAndGet()
            "$dish, plated"
        }
        assertThat(plates).isEqualTo(dishes.associateWith { "$it, plated" })
        assertThat(peak.get()).`as`("dishes cooking at once").isEqualTo(4)
        assertThat(currentTime).`as`("virtual ms: 12 dishes / 4 helpers x 100 ms").isEqualTo(300)
    }

    @Test
    fun `every dish is cooked exactly once`() = runTest {
        val calls = ConcurrentHashMap<String, AtomicInteger>()
        val dishes = (1..50).map { "dish-$it" }
        cookAll(dishes, helpers = 7) { dish ->
            calls.computeIfAbsent(dish) { AtomicInteger() }.incrementAndGet()
            delay((dish.removePrefix("dish-").toLong() % 5) * 10)
            dish
        }
        assertThat(calls.keys).containsExactlyInAnyOrderElementsOf(dishes)
        assertThat(calls.values.map { it.get() }).containsOnly(1)
    }

    @Test
    fun `a dish that fails fails the call and stops the other helpers`() = runTest {
        val finished = CopyOnWriteArrayList<String>()
        val thrown = runCatching {
            cookAll((1..8).map { "dish-$it" }, helpers = 4) { dish ->
                if (dish == "dish-2") { delay(50); throw IOException("the oven for dish-2 broke") }
                delay(1_000)
                finished += dish
                dish
            }
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IOException::class.java).hasMessage("the oven for dish-2 broke")
        assertThat(finished).`as`("dishes that finished after the failure").isEmpty()
        assertThat(currentTime).isEqualTo(50)
    }

    // ---- readings(): callbackFlow ----

    private class FakeProbe : OvenProbe {
        val listeners = CopyOnWriteArrayList<(Reading) -> Unit>()
        val unregistered = AtomicInteger()
        override fun register(listener: (Reading) -> Unit): Registration {
            listeners += listener
            return Registration { listeners -= listener; unregistered.incrementAndGet() }
        }
        fun publish(r: Reading) = listeners.forEach { it(r) }
    }

    @Test
    fun `readings delivers what the probe publishes, then unregisters when the collector stops`() = runTest {
        val probe = FakeProbe()
        val received = CopyOnWriteArrayList<Reading>()
        val collector = backgroundScope.launch { probe.readings().take(2).toList(received) }
        runCurrent()
        assertThat(probe.listeners).`as`("listeners registered once collecting").hasSize(1)

        probe.publish(Reading("roast", 54))
        probe.publish(Reading("roast", 61))
        runCurrent()

        assertThat(received).containsExactly(Reading("roast", 54), Reading("roast", 61))
        assertThat(collector.isCompleted).isTrue()
        assertThat(probe.unregistered.get()).`as`("unregister calls").isEqualTo(1)
        assertThat(probe.listeners).isEmpty()
    }

    @Test
    fun `cancelling the collector unregisters the listener`() = runTest {
        val probe = FakeProbe()
        val collector = backgroundScope.launch { probe.readings().collect { } }
        runCurrent()
        assertThat(probe.listeners).hasSize(1)
        collector.cancel()
        runCurrent()
        assertThat(probe.unregistered.get()).isEqualTo(1)
    }

    // ---- firstOffer: select ----

    private fun shop(name: String, ms: Long, price: Int, cancelled: MutableList<String>): suspend () -> Offer = {
        try { delay(ms); Offer(name, price) } catch (e: kotlin.coroutines.cancellation.CancellationException) { cancelled += name; throw e }
    }

    @Test
    fun `firstOffer returns the first offer to arrive and cancels the others`() = runTest {
        val cancelled = CopyOnWriteArrayList<String>()
        val offer = firstOffer(listOf(
            shop("corner shop", 300, 180, cancelled),
            shop("market", 120, 210, cancelled),
            shop("farm stall", 200, 150, cancelled),
        ))
        assertThat(offer).isEqualTo(Offer("market", 210))
        assertThat(currentTime).`as`("virtual ms").isEqualTo(120)
        assertThat(cancelled).containsExactlyInAnyOrder("corner shop", "farm stall")
    }

    @Test
    fun `firstOffer fails when the first to answer fails`() = runTest {
        val cancelled = CopyOnWriteArrayList<String>()
        val thrown = runCatching {
            firstOffer(listOf(
                shop("corner shop", 300, 180, cancelled),
                { delay(80); throw IOException("the market's line is dead") },
            ))
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IOException::class.java).hasMessage("the market's line is dead")
        assertThat(currentTime).isEqualTo(80)
        assertThat(cancelled).containsExactly("corner shop")
    }
}
