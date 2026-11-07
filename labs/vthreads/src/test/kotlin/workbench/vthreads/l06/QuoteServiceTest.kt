package workbench.vthreads.l06

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.math.BigDecimal
import java.time.Duration
import java.util.concurrent.ConcurrentHashMap
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Semaphore
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread

class QuoteServiceTest {

    /**
     * A fake customer database behind a pool of [poolSize] connections. Like a real pool, a caller
     * that finds no free connection waits up to [borrowTimeoutMs] and then fails. The fake counts
     * both, and it records how many connections were in use at once.
     */
    class FakeDb(
        override val poolSize: Int,
        private val queryMs: Long = 5,
        private val borrowTimeoutMs: Long = 30,
        private val gate: CountDownLatch? = null,
    ) : CustomerDb {
        private val connections = Semaphore(poolSize)
        val inUse = AtomicInteger()
        val peakInUse = AtomicInteger()
        val waitedForConnection = AtomicInteger()
        val timedOut = AtomicInteger()

        override fun tier(customerId: String): String {
            if (!connections.tryAcquire()) {                        // no free connection: wait inside the pool
                waitedForConnection.incrementAndGet()
                if (!connections.tryAcquire(borrowTimeoutMs, TimeUnit.MILLISECONDS)) {
                    timedOut.incrementAndGet()
                    throw IllegalStateException("connection pool: no connection after $borrowTimeoutMs ms")
                }
            }
            peakInUse.accumulateAndGet(inUse.incrementAndGet()) { a, b -> maxOf(a, b) }
            try {
                gate?.await()
                Thread.sleep(queryMs)
                return if (customerId.endsWith("7")) "gold" else "standard"
            } finally {
                inUse.decrementAndGet()
                connections.release()
            }
        }
    }

    /** A fake FX provider: each call sleeps, and the fake records threads and calls in flight. */
    class FakeFx(private val callMs: Long = 100) : FxApi {
        val inside = AtomicInteger()
        val peak = AtomicInteger()
        val threads: MutableSet<Thread> = ConcurrentHashMap.newKeySet()
        val virtualCalls = AtomicInteger()

        override fun rate(pair: String): BigDecimal {
            val me = Thread.currentThread()
            threads += me
            if (me.isVirtual) virtualCalls.incrementAndGet()
            peak.accumulateAndGet(inside.incrementAndGet()) { a, b -> maxOf(a, b) }
            try {
                Thread.sleep(callMs)
                return BigDecimal("1.0842")
            } finally {
                inside.decrementAndGet()
            }
        }
    }

    private fun requests(n: Int) = List(n) { QuoteRequest("cust-$it", "EURUSD", BigDecimal("1000.00")) }

    @Test
    fun `each request runs on its own new virtual thread`() {
        val fx = FakeFx()
        val quotes = QuoteService(FakeDb(poolSize = 10), fx).use { it.quoteAll(requests(200)) }
        assertThat(quotes).hasSize(200)
        assertThat(quotes[7].fee).isEqualByComparingTo("1.00")               // cust-7 is gold
        assertThat(quotes[8].fee).isEqualByComparingTo("2.50")
        assertThat(fx.virtualCalls.get()).describedAs("FX calls made on a virtual thread").isEqualTo(200)
        assertThat(fx.threads).describedAs("distinct threads: one per request, never reused").hasSize(200)
    }

    @Test
    fun `FX calls are no longer capped by the size of a thread pool`() {
        val fx = FakeFx()
        QuoteService(FakeDb(poolSize = 10), fx).use { it.quoteAll(requests(300)) }
        // the old pool allowed 10; the margin is wide so a busy machine can't fail it
        assertThat(fx.peak.get()).describedAs("FX calls in flight at once").isGreaterThan(10)
    }

    @Test
    fun `a burst of 300 requests never waits inside the connection pool`() {
        val db = FakeDb(poolSize = 10)
        val quotes = QuoteService(db, FakeFx()).use { it.quoteAll(requests(300)) }
        assertThat(quotes).hasSize(300)
        assertThat(db.timedOut.get()).describedAs("connection pool timeouts").isZero()
        assertThat(db.waitedForConnection.get()).describedAs("requests that waited inside the pool").isZero()
        assertThat(db.peakInUse.get()).describedAs("connections in use at once").isLessThanOrEqualTo(10)
    }

    @Test
    fun `the database limit follows the pool size, not a hard-coded number`() {
        val db = FakeDb(poolSize = 3)
        val quotes = QuoteService(db, FakeFx()).use { it.quoteAll(requests(60)) }
        assertThat(quotes).hasSize(60)
        assertThat(db.waitedForConnection.get()).describedAs("requests that waited inside the pool").isZero()
        assertThat(db.peakInUse.get()).describedAs("connections in use at once").isBetween(2, 3)
    }

    @Test
    fun `dbWaiting reports how many requests are queued for the database`() {
        val gate = CountDownLatch(1)
        val db = FakeDb(poolSize = 2, gate = gate)
        QuoteService(db, FakeFx(callMs = 1)).use { service ->
            var result: Result<List<Quote>>? = null
            val burst = thread { result = runCatching { service.quoteAll(requests(12)) } }
            try {
                // 2 requests hold both connections behind the gate; the other 10 queue for a permit
                val deadline = System.nanoTime() + Duration.ofSeconds(5).toNanos()
                while (service.dbWaiting() < 10 && System.nanoTime() < deadline) Thread.sleep(5)
                assertThat(service.dbWaiting()).describedAs("requests waiting for a database permit").isEqualTo(10)
                assertThat(db.inUse.get()).describedAs("connections in use").isEqualTo(2)
            } finally {
                gate.countDown()
                burst.join()
            }
            assertThat(result!!.getOrThrow()).hasSize(12)
            assertThat(service.dbWaiting()).describedAs("waiting after the burst").isZero()
        }
    }
}
