package workbench.coroutines.l04

import kotlinx.coroutines.CoroutineName
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.currentCoroutineContext
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration.Companion.seconds

class DispatchersTest {
    // two named single-thread dispatchers stand in for IO and Default, so the test can see where code ran
    private val ioPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-io") }
    private val cpuPool = Executors.newSingleThreadExecutor { r -> Thread(r, "test-cpu") }
    private val io = ioPool.asCoroutineDispatcher()
    private val cpu = cpuPool.asCoroutineDispatcher()

    @AfterEach
    fun closePools() {
        io.close()
        cpu.close()
    }

    private class RecordingStore(val threads: MutableList<String>) : BlockingStatementStore {
        override fun loadRows(accountId: String): List<LedgerRow> {
            threads += "load:" + Thread.currentThread().name
            return listOf(LedgerRow(accountId, -4_250, "card payment"), LedgerRow(accountId, 120_000, "salary"))
        }
    }

    private class RecordingRenderer(val threads: MutableList<String>) : StatementRenderer {
        override fun render(rows: List<LedgerRow>): ByteArray {
            threads += "render:" + Thread.currentThread().name
            return rows.joinToString("\n") { "${it.description};${it.amountCents}" }.toByteArray()
        }
    }

    // ---- StatementService ----

    @Test
    fun `statementPdf loads rows on the IO dispatcher and renders on the CPU dispatcher`() = runTest {
        val threads = CopyOnWriteArrayList<String>()
        val service = StatementService(RecordingStore(threads), RecordingRenderer(threads), io, cpu)

        val pdf = service.statementPdf("acc-77")

        assertThat(String(pdf)).isEqualTo("card payment;-4250\nsalary;120000")
        assertThat(threads).containsExactly("load:test-io", "render:test-cpu")
    }

    @Test
    fun `statementPdf hands the result back on the caller's thread`() = runBlocking {
        val threads = CopyOnWriteArrayList<String>()
        val service = StatementService(RecordingStore(threads), RecordingRenderer(threads), io, cpu)
        val callerThread = Thread.currentThread().name

        service.statementPdf("acc-77")

        assertThat(Thread.currentThread().name).isEqualTo(callerThread)
        assertThat(threads).doesNotContain("load:$callerThread", "render:$callerThread")
    }

    // ---- issuerDispatcher ----

    @Test
    fun `issuerDispatcher is named issuer`() {
        assertThat(issuerDispatcher().toString()).isEqualTo("issuer")
    }

    @Test
    fun `issuerDispatcher lets 20 blocking calls run at the same time`() = runBlocking {
        val dispatcher = issuerDispatcher()
        val allIn = CountDownLatch(20)
        val met = withTimeout(10.seconds) {
            (1..20).map {
                async(dispatcher) {
                    allIn.countDown()
                    allIn.await(5, TimeUnit.SECONDS) // only true if all 20 are blocked here together
                }
            }.awaitAll()
        }
        assertThat(met).`as`("calls that saw all 20 running together").containsOnly(true)
    }

    @Test
    fun `issuerDispatcher never runs more than 20 calls at once`() = runBlocking {
        val dispatcher = issuerDispatcher()
        val active = AtomicInteger()
        val peak = AtomicInteger()
        withTimeout(10.seconds) {
            coroutineScope {
                repeat(60) {
                    launch(dispatcher) {
                        val now = active.incrementAndGet()
                        peak.accumulateAndGet(now, ::maxOf)
                        Thread.sleep(30) // a blocking issuer call
                        active.decrementAndGet()
                    }
                }
            }
        }
        assertThat(peak.get()).`as`("peak concurrent calls").isLessThanOrEqualTo(20).isGreaterThan(1)
    }

    // ---- context elements ----

    @Test
    fun `withPaymentTrace makes the trace id visible inside the block`() = runTest {
        assertThat(currentTraceId()).isNull()
        val seen = withPaymentTrace("tr-9f2") { currentTraceId() }
        assertThat(seen).isEqualTo("tr-9f2")
        assertThat(currentTraceId()).`as`("after the block").isNull()
    }

    @Test
    fun `withPaymentTrace names the coroutine and child coroutines inherit both elements`() = runTest {
        val seen = CopyOnWriteArrayList<String>()
        withPaymentTrace("tr-9f2") {
            launch {
                val ctx = currentCoroutineContext()
                seen += "${ctx[PaymentTrace]?.traceId} ${ctx[CoroutineName]?.name}"
            }
        }
        assertThat(seen).containsExactly("tr-9f2 payment-tr-9f2")
    }

    @Test
    fun `a nested withPaymentTrace replaces the outer trace for its block only`() = runTest {
        val seen = withPaymentTrace("outer") {
            val inner = withPaymentTrace("inner") { currentTraceId() }
            listOf(inner, currentTraceId())
        }
        assertThat(seen).containsExactly("inner", "outer")
    }
}
