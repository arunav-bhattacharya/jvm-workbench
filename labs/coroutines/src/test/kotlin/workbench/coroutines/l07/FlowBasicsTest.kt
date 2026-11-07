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

    // ---- ledgerEntries: a cold, lazy flow ----

    /** Three pages of five entries each. Counts the calls. */
    private class FakeLedger : LedgerApi {
        val calls = CopyOnWriteArrayList<String?>()
        override suspend fun page(accountId: String, cursor: String?): LedgerPage {
            calls += cursor
            val n = when (cursor) { null -> 0; "c1" -> 1; "c2" -> 2; else -> error("unknown cursor $cursor") }
            val entries = (1..5).map { LedgerEntry("e${n * 5 + it}", 100L * (n * 5 + it)) }
            return LedgerPage(entries, if (n < 2) "c${n + 1}" else null)
        }
    }

    @Test
    fun `ledgerEntries calls nothing until it is collected, then reads every page in order`() = runTest {
        val api = FakeLedger()
        val entries = ledgerEntries(api, "acc-1")
        assertThat(api.calls).`as`("calls made by building the flow").isEmpty()

        val ids = entries.toList().map { it.id }
        assertThat(ids).containsExactlyElementsOf((1..15).map { "e$it" })
        assertThat(api.calls).containsExactly(null, "c1", "c2")
    }

    @Test
    fun `taking three entries fetches only the first page`() = runTest {
        val api = FakeLedger()
        val ids = ledgerEntries(api, "acc-1").take(3).toList().map { it.id }
        assertThat(ids).containsExactly("e1", "e2", "e3")
        assertThat(api.calls).`as`("pages fetched").containsExactly(null)
    }

    @Test
    fun `every collection starts again from the first page`() = runTest {
        val api = FakeLedger()
        val entries = ledgerEntries(api, "acc-1")
        entries.toList()
        entries.toList()
        assertThat(api.calls).containsExactly(null, "c1", "c2", null, "c1", "c2")
    }

    // ---- settlementRecords: blocking upstream, flowOn ----

    private val ioPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-io") }

    // tests run with -ea, which turns on coroutine debug mode: it adds " @coroutine#N" to thread names
    private fun threadName() = Thread.currentThread().name.substringBefore(" @")
    private val io = ioPool.asCoroutineDispatcher()

    @AfterEach
    fun closePool() = io.close()

    @Test
    fun `settlementRecords reads on the io dispatcher and the collector stays on its own thread`() = runTest {
        val lines = ArrayDeque(listOf("pay-1,4250,EUR", "pay-2,-990,EUR", "pay-3,120000,GBP"))
        val readOn = CopyOnWriteArrayList<String>()
        val reader = LineReader { readOn += threadName(); lines.removeFirstOrNull() }
        val collectedOn = CopyOnWriteArrayList<String>()
        val testThread = threadName()

        val records = mutableListOf<SettlementRecord>()
        settlementRecords(reader, io).collect { collectedOn += threadName(); records += it }

        assertThat(records).containsExactly(
            SettlementRecord("pay-1", 4250, "EUR"), SettlementRecord("pay-2", -990, "EUR"), SettlementRecord("pay-3", 120000, "GBP"),
        )
        assertThat(readOn).`as`("threads that called readLine").containsOnly("test-io")
        assertThat(collectedOn).`as`("threads that ran the collector").containsOnly(testThread)
    }

    // ---- importReport: catch, exception transparency, onCompletion ----

    private fun records(vararg ids: String, failWith: Throwable? = null): Flow<SettlementRecord> = flow {
        for (id in ids) emit(SettlementRecord(id, 100, "EUR"))
        if (failWith != null) throw failWith
    }

    @Test
    fun `importReport imports every record and reports a normal end`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val events = importReport(records("pay-1", "pay-2")) { done += it }.toList()
        assertThat(events).containsExactly(ImportEvent.Imported("pay-1"), ImportEvent.Imported("pay-2"))
        assertThat(done).containsExactly(null)
    }

    @Test
    fun `an upstream failure becomes an Aborted event`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val events = importReport(records("pay-1", "pay-2", failWith = IOException("file truncated"))) { done += it }.toList()
        assertThat(events).containsExactly(
            ImportEvent.Imported("pay-1"), ImportEvent.Imported("pay-2"), ImportEvent.Aborted("file truncated"),
        )
        assertThat(done).hasSize(1)
        assertThat(done[0]).isInstanceOf(IOException::class.java).hasMessage("file truncated")
    }

    @Test
    fun `a failure in the collector reaches the collector unchanged`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val seen = CopyOnWriteArrayList<ImportEvent>()
        val thrown = runCatching {
            importReport(records("pay-1", "pay-2")) { done += it }.collect { event ->
                seen += event
                throw IllegalArgumentException("ledger db down")
            }
        }.exceptionOrNull()
        assertThat(thrown).`as`("what the collector got back").isInstanceOf(IllegalArgumentException::class.java).hasMessage("ledger db down")
        assertThat(seen).`as`("events the collector saw").containsExactly(ImportEvent.Imported("pay-1"))
        assertThat(done).hasSize(1)
        assertThat(done[0]).hasMessage("ledger db down")
    }

    @Test
    fun `importReport reports the end when the collector stops early`() = runTest {
        val done = CopyOnWriteArrayList<Throwable?>()
        val events = importReport(records("pay-1", "pay-2", "pay-3")) { done += it }.take(1).toList()
        assertThat(events).containsExactly(ImportEvent.Imported("pay-1"))
        assertThat(done).hasSize(1)
        assertThat(done[0]).`as`("an early stop is a cancellation").isInstanceOf(CancellationException::class.java)
    }
}
