@file:OptIn(ExperimentalCoroutinesApi::class)

package workbench.flows.l03

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.Executors

class DeliveryImportTest {

    // ---- importDelivery: only the blocking part moves behind flowOn ----

    private val ioPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-io") }
    private val io = ioPool.asCoroutineDispatcher()

    @AfterEach
    fun closePool() = io.close()

    // tests run with -ea, which turns on coroutine debug mode: it adds " @coroutine#N" to thread names
    private fun threadName() = Thread.currentThread().name.substringBefore(" @")

    private fun noteOf(vararg lines: String, readOn: MutableList<String>): LineReader {
        val left = ArrayDeque(lines.toList())
        return LineReader { readOn += threadName(); left.removeFirstOrNull() }
    }

    @Test
    fun `importDelivery reads on io and stores in the collector's context`() = runTest {
        val readOn = CopyOnWriteArrayList<String>()
        val storedOn = CopyOnWriteArrayList<String>()
        val stored = CopyOnWriteArrayList<DeliveryLine>()
        val pantry = Pantry { storedOn += threadName(); stored += it }
        val testThread = threadName()

        val collectedOn = mutableListOf<String>()
        val imported = mutableListOf<DeliveryLine>()
        importDelivery(noteOf("flour,2000,g", "eggs,12,pcs", "milk,1000,ml", readOn = readOn), pantry, io)
            .collect { collectedOn += threadName(); imported += it }

        val expected = listOf(DeliveryLine("flour", 2000, "g"), DeliveryLine("eggs", 12, "pcs"), DeliveryLine("milk", 1000, "ml"))
        assertThat(imported).containsExactlyElementsOf(expected)
        assertThat(stored).containsExactlyElementsOf(expected)
        assertThat(readOn).`as`("threads that called readLine").containsOnly("test-io")
        assertThat(storedOn).`as`("threads that called pantry.store").containsOnly(testThread)
        assertThat(collectedOn).`as`("threads that ran the collector").containsOnly(testThread)
    }

    @Test
    fun `importDelivery reads nothing until it is collected`() = runTest {
        val readOn = CopyOnWriteArrayList<String>()
        importDelivery(noteOf("flour,2000,g", readOn = readOn), Pantry { }, io)
        assertThat(readOn).`as`("reads made by building the flow").isEmpty()
    }

    // ---- bothCooks: two producers, one flow ----

    /** A cook who sends out one plate every [everyMs] of virtual time. */
    private fun cook(name: String, everyMs: Long, vararg dishes: String): Flow<Plate> = flow {
        for (dish in dishes) {
            delay(everyMs)
            emit(Plate(name, dish))
        }
    }

    @Test
    fun `bothCooks delivers both cooks' plates as they are ready and completes after the slower one`() = runTest {
        val grill = cook("grill", 100, "g1", "g2", "g3")    // at 100, 200, 300
        val oven = cook("oven", 130, "o1", "o2", "o3")      // at 130, 260, 390
        val dishes = bothCooks(grill, oven).toList().map { it.dish }
        assertThat(dishes).containsExactly("g1", "o1", "g2", "o2", "g3", "o3")
        assertThat(currentTime).`as`("virtual time when the merged flow completed").isEqualTo(390L)
    }

    @Test
    fun `bothCooks keeps going when one cook has nothing to send`() = runTest {
        val dishes = bothCooks(cook("grill", 100), cook("oven", 50, "o1", "o2")).toList().map { it.dish }
        assertThat(dishes).containsExactly("o1", "o2")
        assertThat(currentTime).isEqualTo(100L)
    }

    @Test
    fun `flow { } refuses emits from a launched coroutine, with a hint to use channelFlow`() = runTest {
        val broken = flow {
            coroutineScope { launch { emit(1) } }
        }
        val thrown = runCatching { broken.toList() }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IllegalStateException::class.java)
            .hasMessageContaining("Emission from another coroutine is detected")
            .hasMessageContaining("please use 'channelFlow' builder instead of 'flow'")
    }
}
