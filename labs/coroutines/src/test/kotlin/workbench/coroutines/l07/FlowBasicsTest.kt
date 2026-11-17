package workbench.coroutines.l07

import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.take
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Test
import java.io.IOException
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.Executors
import kotlin.coroutines.cancellation.CancellationException

class FlowBasicsTest {

    // ---- aisleItems: a cold, lazy flow ----

    /** Three pages of five items each. Counts the calls. */
    private class FakeShop : GroceryShop {
        val calls = CopyOnWriteArrayList<String?>()
        override suspend fun page(aisle: String, cursor: String?): ItemPage {
            calls += cursor
            val n = when (cursor) { null -> 0; "c1" -> 1; "c2" -> 2; else -> error("unknown cursor $cursor") }
            val items = (1..5).map { Item("i${n * 5 + it}", 100L * (n * 5 + it)) }
            return ItemPage(items, if (n < 2) "c${n + 1}" else null)
        }
    }

    @Test
    fun `aisleItems calls nothing until it is collected, then reads every page in order`() = runTest {
        val shop = FakeShop()
        val items = aisleItems(shop, "fruit")
        assertThat(shop.calls).`as`("calls made by building the flow").isEmpty()

        val names = items.toList().map { it.name }
        assertThat(names).containsExactlyElementsOf((1..15).map { "i$it" })
        assertThat(shop.calls).containsExactly(null, "c1", "c2")
    }

    @Test
    fun `taking three items fetches only the first page`() = runTest {
        val shop = FakeShop()
        val names = aisleItems(shop, "fruit").take(3).toList().map { it.name }
        assertThat(names).containsExactly("i1", "i2", "i3")
        assertThat(shop.calls).`as`("pages fetched").containsExactly(null)
    }

    @Test
    fun `every collection starts again from the first page`() = runTest {
        val shop = FakeShop()
        val items = aisleItems(shop, "fruit")
        items.toList()
        items.toList()
        assertThat(shop.calls).containsExactly(null, "c1", "c2", null, "c1", "c2")
    }

    // ---- deliveryLines: blocking upstream, flowOn ----

    private val ioPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-io") }

    // tests run with -ea, which turns on coroutine debug mode: it adds " @coroutine#N" to thread names
    private fun threadName() = Thread.currentThread().name.substringBefore(" @")
    private val io = ioPool.asCoroutineDispatcher()

    @AfterEach
    fun closePool() = io.close()

    @Test
    fun `deliveryLines reads on the io dispatcher and the collector stays on its own thread`() = runTest {
        val lines = ArrayDeque(listOf("flour,2000,g", "eggs,12,pcs", "butter,250,g"))
        val readOn = CopyOnWriteArrayList<String>()
        val reader = LineReader { readOn += threadName(); lines.removeFirstOrNull() }
        val collectedOn = CopyOnWriteArrayList<String>()
        val testThread = threadName()

        val delivered = mutableListOf<DeliveryLine>()
        deliveryLines(reader, io).collect { collectedOn += threadName(); delivered += it }

        assertThat(delivered).containsExactly(
            DeliveryLine("flour", 2000, "g"), DeliveryLine("eggs", 12, "pcs"), DeliveryLine("butter", 250, "g"),
        )
        assertThat(readOn).`as`("threads that called readLine").containsOnly("test-io")
        assertThat(collectedOn).`as`("threads that ran the collector").containsOnly(testThread)
    }

    // ---- stockReport: catch, exception transparency, onCompletion ----

    private fun lines(vararg items: String, failWith: Throwable? = null): Flow<DeliveryLine> = flow {
        for (item in items) emit(DeliveryLine(item, 1, "pcs"))
        if (failWith != null) throw failWith
    }

    @Test
    fun `stockReport stocks every line and reports a normal end`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val events = stockReport(lines("flour", "eggs")) { done += it }.toList()
        assertThat(events).containsExactly(StockEvent.Stocked("flour"), StockEvent.Stocked("eggs"))
        assertThat(done).containsExactly(null)
    }

    @Test
    fun `an upstream failure becomes an Aborted event`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val events = stockReport(lines("flour", "eggs", failWith = IOException("delivery note torn"))) { done += it }.toList()
        assertThat(events).containsExactly(
            StockEvent.Stocked("flour"), StockEvent.Stocked("eggs"), StockEvent.Aborted("delivery note torn"),
        )
        assertThat(done).hasSize(1)
        assertThat(done[0]).isInstanceOf(IOException::class.java).hasMessage("delivery note torn")
    }

    @Test
    fun `a failure in the collector reaches the collector unchanged`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val seen = CopyOnWriteArrayList<StockEvent>()
        val thrown = runCatching {
            stockReport(lines("flour", "eggs")) { done += it }.collect { event ->
                seen += event
                throw IllegalArgumentException("pantry shelf full")
            }
        }.exceptionOrNull()
        assertThat(thrown).`as`("what the collector got back").isInstanceOf(IllegalArgumentException::class.java).hasMessage("pantry shelf full")
        assertThat(seen).`as`("events the collector saw").containsExactly(StockEvent.Stocked("flour"))
        assertThat(done).hasSize(1)
        assertThat(done[0]).hasMessage("pantry shelf full")
    }

    @Test
    fun `stockReport reports the end when the collector stops early`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val events = stockReport(lines("flour", "eggs", "butter")) { done += it }.take(1).toList()
        assertThat(events).containsExactly(StockEvent.Stocked("flour"))
        assertThat(done).hasSize(1)
        assertThat(done[0]).`as`("an early stop is a cancellation").isInstanceOf(CancellationException::class.java)
    }
}
