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

class SettlementImportTest {

    // ---- importSettlements: only the blocking part moves behind flowOn ----

    private val ioPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-io") }
    private val io = ioPool.asCoroutineDispatcher()

    @AfterEach
    fun closePool() = io.close()

    // tests run with -ea, which turns on coroutine debug mode: it adds " @coroutine#N" to thread names
    private fun threadName() = Thread.currentThread().name.substringBefore(" @")

    private fun fileOf(vararg lines: String, readOn: MutableList<String>): LineReader {
        val left = ArrayDeque(lines.toList())
        return LineReader { readOn += threadName(); left.removeFirstOrNull() }
    }

    @Test
    fun `importSettlements reads on io and posts in the collector's context`() = runTest {
        val readOn = CopyOnWriteArrayList<String>()
        val postedOn = CopyOnWriteArrayList<String>()
        val posted = CopyOnWriteArrayList<Settlement>()
        val ledger = Ledger { postedOn += threadName(); posted += it }
        val testThread = threadName()

        val collectedOn = mutableListOf<String>()
        val imported = mutableListOf<Settlement>()
        importSettlements(fileOf("pay-1,4250,EUR", "pay-2,990,EUR", "pay-3,12000,GBP", readOn = readOn), ledger, io)
            .collect { collectedOn += threadName(); imported += it }

        val expected = listOf(Settlement("pay-1", 4250, "EUR"), Settlement("pay-2", 990, "EUR"), Settlement("pay-3", 12000, "GBP"))
        assertThat(imported).containsExactlyElementsOf(expected)
        assertThat(posted).containsExactlyElementsOf(expected)
        assertThat(readOn).`as`("threads that called readLine").containsOnly("test-io")
        assertThat(postedOn).`as`("threads that called ledger.post").containsOnly(testThread)
        assertThat(collectedOn).`as`("threads that ran the collector").containsOnly(testThread)
    }

    @Test
    fun `importSettlements reads nothing until it is collected`() = runTest {
        val readOn = CopyOnWriteArrayList<String>()
        importSettlements(fileOf("pay-1,4250,EUR", readOn = readOn), Ledger { }, io)
        assertThat(readOn).`as`("reads made by building the flow").isEmpty()
    }

    // ---- bothAcquirers: two producers, one flow ----

    /** A feed that emits one authorization every [everyMs] of virtual time. */
    private fun feed(acquirer: String, everyMs: Long, vararg ids: String): Flow<Authorization> = flow {
        for (id in ids) {
            delay(everyMs)
            emit(Authorization(acquirer, id))
        }
    }

    @Test
    fun `bothAcquirers delivers both feeds as they arrive and completes after the slower one`() = runTest {
        val north = feed("north", 100, "n1", "n2", "n3")    // at 100, 200, 300
        val east = feed("east", 130, "e1", "e2", "e3")      // at 130, 260, 390
        val ids = bothAcquirers(north, east).toList().map { it.paymentId }
        assertThat(ids).containsExactly("n1", "e1", "n2", "e2", "n3", "e3")
        assertThat(currentTime).`as`("virtual time when the merged flow completed").isEqualTo(390L)
    }

    @Test
    fun `bothAcquirers keeps going when one feed is empty`() = runTest {
        val ids = bothAcquirers(feed("north", 100), feed("east", 50, "e1", "e2")).toList().map { it.paymentId }
        assertThat(ids).containsExactly("e1", "e2")
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
