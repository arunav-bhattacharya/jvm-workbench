package workbench.quotes.l03

import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.async
import kotlinx.coroutines.awaitAll
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import java.io.IOException
import java.net.ConnectException
import java.net.InetAddress
import java.net.Socket
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ExecutionException
import java.util.concurrent.TimeUnit
import kotlin.concurrent.thread
import kotlin.random.Random
import kotlin.text.Charsets.UTF_8
import kotlin.time.Duration
import kotlin.time.Duration.Companion.hours
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.minutes
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
@Timeout(30)
class UnderLoadTest {

    private fun TestScope.fake(
        name: String,
        idempotent: Boolean = true,
        cancelled: MutableList<String> = CopyOnWriteArrayList(),
        script: (Int) -> Pair<Duration, Exception?>,
    ) = FakeProvider(name, idempotent, clock = { testScheduler.currentTime }, cancelled = cancelled, script = script)

    // ---- the bulkhead ----

    @Test
    fun `each provider sees at most its limit of calls at once`() = runTest {
        val northbank = fake("northbank") { 100.milliseconds to null }
        val guarded = GuardedProvider(northbank, maxConcurrent = 4)
        val quotes = List(50) { async { guarded.quote("EURUSD") } }.awaitAll()
        assertThat(quotes).hasSize(50)
        assertThat(northbank.peak.get()).`as`("calls in flight at once").isEqualTo(4)
        assertThat(currentTime).`as`("virtual ms: 50 calls, 4 at a time, 100 ms each").isEqualTo(1_300)
    }

    @Test
    fun `the limit counts hedges too`() = runTest {
        val northbank = fake("northbank") { n -> (if (n == 1) 1_000 else 30).milliseconds to null }
        val guarded = GuardedProvider(northbank, maxConcurrent = 1, hedgeAfter = 100.milliseconds)
        guarded.quote("EURUSD")
        assertThat(northbank.peak.get()).`as`("calls in flight at once, with a hedge waiting").isEqualTo(1)
        assertThat(currentTime).`as`("the hedge had no permit, so the first call won").isEqualTo(1_000)
    }

    // ---- retries ----

    @Test
    fun `an idempotent provider is retried after a transient failure, with growing waits`() = runTest {
        val eastgate = fake("eastgate") { n -> 10.milliseconds to (if (n < 3) IOException("eastgate 503") else null) }
        val guarded = GuardedProvider(eastgate, 8, Backoff(retries = 2, first = 100.milliseconds, jitter = 0.0))
        assertThat(guarded.quote("EURUSD").provider).isEqualTo("eastgate")
        assertThat(eastgate.started).`as`("virtual ms of each attempt: waits of 100, then 200").containsExactly(0L, 110L, 320L)
    }

    @Test
    fun `the last failure reaches the caller, and errors that are not IOException are not retried`() = runTest {
        val down = fake("eastgate") { 10.milliseconds to IOException("eastgate 503") }
        val thrown = runCatching { GuardedProvider(down, 8, Backoff(retries = 2, jitter = 0.0)).quote("EURUSD") }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IOException::class.java).hasMessage("eastgate 503")
        assertThat(down.calls.get()).`as`("one call and two retries").isEqualTo(3)

        val wrong = fake("eastgate") { 10.milliseconds to IllegalArgumentException("unknown symbol") }
        runCatching { GuardedProvider(wrong, 8, Backoff(retries = 2, jitter = 0.0)).quote("XXXYYY") }
        assertThat(wrong.calls.get()).`as`("a bad request is not worth repeating").isEqualTo(1)
    }

    @Test
    fun `a provider that is not idempotent is called once, never retried or hedged`() = runTest {
        val fjord = fake("fjord", idempotent = false) { 300.milliseconds to IOException("fjord 503") }
        val guarded = GuardedProvider(fjord, 8, Backoff(retries = 2, jitter = 0.0), hedgeAfter = 50.milliseconds)
        val thrown = runCatching { guarded.quote("EURUSD") }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IOException::class.java)
        assertThat(fjord.calls.get()).`as`("calls to a provider whose quotes are firm").isEqualTo(1)
    }

    @Test
    fun `jitter moves each wait to between half and one and a half times the nominal wait`() = runTest {
        val firstWaits = (1..10).map { seed ->
            val start = currentTime
            var attempts = 0
            retrying(Backoff(retries = 1, first = 100.milliseconds, jitter = 0.5), Random(seed)) {
                if (++attempts == 1) throw IOException("503") else "ok"
            }
            currentTime - start
        }
        assertThat(firstWaits).`as`("first waits for ten clients, virtual ms").allSatisfy { assertThat(it).isBetween(50L, 150L) }
        assertThat(firstWaits.toSet()).`as`("distinct waits among ten clients").hasSizeGreaterThanOrEqualTo(5)
    }

    // ---- the hedge ----

    @Test
    fun `a call slower than hedgeAfter gets one hedge, and the first answer wins`() = runTest {
        val northbank = fake("northbank") { n -> (if (n == 1) 1_000 else 30).milliseconds to null }
        val guarded = GuardedProvider(northbank, 8, hedgeAfter = 100.milliseconds)
        assertThat(guarded.quote("EURUSD").provider).isEqualTo("northbank")
        assertThat(currentTime).`as`("virtual ms: the hedge starts at 100 and answers 30 ms later").isEqualTo(130)
        assertThat(northbank.calls.get()).isEqualTo(2)
        assertThat(northbank.cancelledCalls).`as`("the slow first call was cancelled").containsExactly(1)
    }

    @Test
    fun `a call that answers before hedgeAfter is never hedged`() = runTest {
        val northbank = fake("northbank") { 40.milliseconds to null }
        GuardedProvider(northbank, 8, hedgeAfter = 100.milliseconds).quote("EURUSD")
        assertThat(northbank.calls.get()).isEqualTo(1)
        assertThat(currentTime).isEqualTo(40)
    }

    // ---- admission and shutdown ----

    @Test
    fun `requests beyond maxInFlight are shed at once with a clear error`() = runTest {
        val northbank = fake("northbank") { 200.milliseconds to null }
        val service = QuoteService(StandardTestDispatcher(testScheduler), BestQuote(listOf(northbank), 1.seconds), maxInFlight = 4)
        val futures = List(10) { service.quote("EURUSD") }
        val shed = futures.filter { it.isCompletedExceptionally }
        assertThat(shed).`as`("requests refused at virtual time 0").hasSize(6)
        shed.forEach { f -> assertThatThrownBy { f.get() }.hasCauseInstanceOf(BusyException::class.java).hasMessageContaining("busy") }
        advanceUntilIdle()
        assertThat(futures.count { it.isDone && !it.isCompletedExceptionally }).`as`("admitted requests answered").isEqualTo(4)
        assertThat(northbank.calls.get()).`as`("provider calls: a shed request never reaches a provider").isEqualTo(4)
        val next = service.quote("EURUSD")
        advanceUntilIdle()
        assertThat(next.get().provider).`as`("permits came back").isEqualTo("northbank")
        service.close()
    }

    @Test
    fun `shutdown lets requests in flight finish within the grace period`() = runTest {
        val northbank = fake("northbank") { 200.milliseconds to null }
        val service = QuoteService(StandardTestDispatcher(testScheduler), BestQuote(listOf(northbank), 1.seconds))
        val a = service.quote("EURUSD")
        val b = service.quote("GBPUSD")
        runCurrent()
        assertThat(service.shutdown(grace = 1.seconds)).`as`("requests cancelled").isZero()
        assertThat(currentTime).`as`("shutdown returned when the last request was done").isEqualTo(200)
        assertThat(listOf(a.get().symbol, b.get().symbol)).containsExactly("EURUSD", "GBPUSD")
        assertThatThrownBy { service.quote("EURUSD").get() }.isInstanceOf(ExecutionException::class.java)
            .hasCauseInstanceOf(ShuttingDownException::class.java)
        assertThat(service.inFlight).isZero()
    }

    @Test
    fun `shutdown cancels what still runs after the grace period and leaves no coroutines behind`() = runTest {
        val cancelled = CopyOnWriteArrayList<String>()
        val hanging = listOf("northbank", "eastgate", "fjord").map { fake(it, cancelled = cancelled) { 1.hours to null } }
        val service = QuoteService(StandardTestDispatcher(testScheduler), BestQuote(hanging, 1.minutes))
        val a = service.quote("EURUSD")
        val b = service.quote("GBPUSD")
        runCurrent()
        assertThat(service.shutdown(grace = 500.milliseconds)).`as`("requests cancelled").isEqualTo(2)
        assertThat(currentTime).isEqualTo(500)
        assertThat(a.isCancelled && b.isCancelled).`as`("both futures cancelled").isTrue()
        assertThat(cancelled).`as`("provider calls cancelled").hasSize(6)
        assertThat(service.inFlight).`as`("coroutines left in the service").isZero()
    }

    // ---- the whole program over TCP ----

    private class Client(port: Int) : AutoCloseable {
        val socket = Socket(InetAddress.getLoopbackAddress(), port).apply { soTimeout = 5_000 }
        val reader = socket.getInputStream().bufferedReader(UTF_8)
        fun send(vararg lines: String) = socket.getOutputStream().run { write(lines.joinToString("\n", postfix = "\n").toByteArray(UTF_8)); flush() }
        override fun close() = socket.close()
    }

    private class Gated(override val name: String, private val gate: CompletableDeferred<Unit>, private val started: CountDownLatch) : Provider {
        override val idempotent = true
        override suspend fun quote(symbol: String): Quote {
            started.countDown()
            gate.await()
            return Quote.live(symbol, "1.0842", name)
        }
    }

    @Test
    fun `over TCP, a request beyond the limit gets ERR busy at once`() {
        val gate = CompletableDeferred<Unit>()
        val started = CountDownLatch(2)
        val app = QuoteApp(listOf(Gated("northbank", gate, started)), deadline = 10.seconds, maxInFlight = 2)
        try {
            Client(app.port()).use { c ->
                c.send("1 EURUSD", "2 EURUSD")
                assertThat(started.await(5, TimeUnit.SECONDS)).`as`("two requests admitted").isTrue()
                c.send("3 EURUSD")
                assertThat(c.reader.readLine()).isEqualTo("3 ERR busy")
                gate.complete(Unit)
                assertThat(setOf(c.reader.readLine(), c.reader.readLine()))
                    .containsExactlyInAnyOrder("1 OK EURUSD 1.0842 northbank", "2 OK EURUSD 1.0842 northbank")
            }
        } finally {
            gate.complete(Unit)
            app.shutdown(1.seconds)
        }
    }

    @Test
    fun `over TCP, shutdown answers the request in flight, then closes the connection`() {
        val started = CountDownLatch(1)
        val slow = object : Provider {
            override val name = "northbank"
            override val idempotent = true
            override suspend fun quote(symbol: String): Quote {
                started.countDown()
                delay(300)
                return Quote.live(symbol, "1.0842", name)
            }
        }
        val app = QuoteApp(listOf(slow), deadline = 10.seconds, maxInFlight = 16)
        val port = app.port()
        Client(port).use { c ->
            c.send("1 EURUSD")
            assertThat(started.await(5, TimeUnit.SECONDS)).isTrue()
            val stopper = thread { app.shutdown(grace = 5.seconds) }
            assertThat(c.reader.readLine()).`as`("the reply to the request in flight").isEqualTo("1 OK EURUSD 1.0842 northbank")
            assertThat(c.reader.readLine()).`as`("then the server closes the connection").isNull()
            stopper.join(10_000)
            assertThat(stopper.isAlive).`as`("shutdown still running").isFalse()
        }
        assertThatThrownBy { Socket(InetAddress.getLoopbackAddress(), port).close() }.isInstanceOf(ConnectException::class.java)
    }
}
