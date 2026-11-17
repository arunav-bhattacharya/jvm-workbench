package workbench.quotes.l02

import io.netty.channel.MultiThreadIoEventLoopGroup
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.awaitCancellation
import kotlinx.coroutines.delay
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withTimeout
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.Timeout
import java.io.IOException
import java.math.BigDecimal
import java.net.InetAddress
import java.net.Socket
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.ExecutionException
import java.util.concurrent.TimeUnit
import kotlin.coroutines.cancellation.CancellationException
import kotlin.text.Charsets.UTF_8
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
@Timeout(30)
class FanOutTest {
    private val cancelled = CopyOnWriteArrayList<String>()

    private fun northline(ms: Long = 120, failure: Exception? = null) = FakeProvider("northline", "12.45", ms.milliseconds, failure, cancelled)
    private fun eastgate(ms: Long = 300) = FakeProvider("eastgate", "12.41", ms.milliseconds, cancelled = cancelled)
    private fun fjord(ms: Long = 200, failure: Exception? = null) = FakeProvider("fjord", "12.43", ms.milliseconds, failure, cancelled)

    // ---- BestQuote: the fan-out, on virtual time ----

    @Test
    fun `asks all three at once and keeps the lowest price, in the time of the slowest`() = runTest {
        val best = BestQuote(listOf(northline(), eastgate(), fjord()), deadline = 1.seconds)
        val quote = best.quote("LISBON")
        assertThat(quote).isEqualTo(Quote.live("LISBON", "12.41", "eastgate"))
        assertThat(currentTime).`as`("virtual ms: the slowest call, not the sum").isEqualTo(300)
    }

    @Test
    fun `a provider that fails does not cancel the other two`() = runTest {
        val best = BestQuote(listOf(northline(50, IOException("northline 503")), eastgate(), fjord()), deadline = 1.seconds)
        assertThat(best.quote("LISBON").provider).isEqualTo("eastgate")
        assertThat(cancelled).`as`("provider calls cancelled").isEmpty()
        assertThat(currentTime).isEqualTo(300)
    }

    @Test
    fun `a provider slower than the deadline is cancelled at the deadline, and the others still count`() = runTest {
        val best = BestQuote(listOf(northline(), eastgate(1_000), fjord()), deadline = 300.milliseconds)
        val quote = best.quote("LISBON")
        assertThat(quote).isEqualTo(Quote.live("LISBON", "12.43", "fjord"))
        assertThat(currentTime).`as`("virtual ms: the deadline").isEqualTo(300)
        assertThat(cancelled).containsExactly("eastgate")
    }

    @Test
    fun `a provider whose own client times out counts as no answer`() = runTest {
        val ownTimeout = object : Provider {
            override val name = "fjord"
            override suspend fun quote(destination: String): Quote =
                withTimeout(50) { delay(1_000); Quote.live(destination, "12.00", name) }   // its client gives up at 50 ms
        }
        val best = BestQuote(listOf(northline(), ownTimeout, eastgate()), deadline = 1.seconds)
        assertThat(best.quote("LISBON").provider).isEqualTo("eastgate")
        assertThat(currentTime).isEqualTo(300)
    }

    @Test
    fun `when nobody answers in time, the last good quote is served, marked stale`() = runTest {
        val cache = QuoteCache()
        BestQuote(listOf(northline(), eastgate(), fjord()), deadline = 1.seconds, cache = cache).quote("LISBON")
        val start = currentTime
        val down = BestQuote(listOf(northline(5_000), eastgate(5_000), fjord(10, IOException("fjord 503"))), deadline = 300.milliseconds, cache = cache)
        val quote = down.quote("LISBON")
        assertThat(quote).isEqualTo(Quote("LISBON", BigDecimal("12.41"), "eastgate", true))
        assertThat(currentTime - start).`as`("virtual ms until the stale answer").isEqualTo(300)
    }

    @Test
    fun `with no answer and nothing cached, quote fails with NoQuoteException`() = runTest {
        val down = BestQuote(listOf(northline(5_000), eastgate(5_000), fjord(5_000)), deadline = 300.milliseconds)
        val thrown = runCatching { down.quote("ATHENS") }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(NoQuoteException::class.java).hasMessage("no quote for ATHENS")
        assertThat(cancelled).containsExactlyInAnyOrder("northline", "eastgate", "fjord")
    }

    // ---- QuoteService: a future for the Java handler, a coroutine behind it ----

    @Test
    fun `quote returns an unfinished future at once and completes it from the coroutine`() = runTest {
        val service = QuoteService(StandardTestDispatcher(testScheduler), BestQuote(listOf(northline(), eastgate(), fjord()), 1.seconds))
        val future = service.quote("LISBON")
        assertThat(future.isDone).`as`("done before any provider answered").isFalse()
        assertThat(service.inFlight).isEqualTo(1)
        advanceUntilIdle()
        assertThat(future.get().provider).isEqualTo("eastgate")
        assertThat(currentTime).isEqualTo(300)
        assertThat(service.inFlight).isEqualTo(0)
        service.close()
    }

    @Test
    fun `cancelling the future cancels the coroutine and all three provider calls`() = runTest {
        val service = QuoteService(StandardTestDispatcher(testScheduler), BestQuote(listOf(northline(5_000), eastgate(5_000), fjord(5_000)), 10.seconds))
        val future = service.quote("LISBON")
        runCurrent()                                  // the three calls have started
        future.cancel(true)                           // what the handler does in channelInactive
        runCurrent()
        assertThat(cancelled).containsExactlyInAnyOrder("northline", "eastgate", "fjord")
        assertThat(service.inFlight).`as`("request coroutines left").isEqualTo(0)
        assertThat(currentTime).isEqualTo(0)
        service.close()
    }

    @Test
    fun `a failed quote fails only its own future`() = runTest {
        val cache = QuoteCache()
        val flaky = object : Provider {
            var up = false
            override val name = "fjord"
            override suspend fun quote(destination: String): Quote { delay(10); if (up) return Quote.live(destination, "12.43", name) else throw IOException("down") }
        }
        val service = QuoteService(StandardTestDispatcher(testScheduler), BestQuote(listOf(flaky), 1.seconds, cache))
        val first = service.quote("LISBON")
        advanceUntilIdle()
        assertThatThrownBy { first.get() }.isInstanceOf(ExecutionException::class.java).hasCauseInstanceOf(NoQuoteException::class.java)
        flaky.up = true
        val second = service.quote("LISBON")
        advanceUntilIdle()
        assertThat(second.get().provider).`as`("the next request still works").isEqualTo("fjord")
        service.close()
    }

    // ---- end to end: the lesson 1 server with the coroutine source ----

    private class Client(port: Int) : AutoCloseable {
        val socket = Socket(InetAddress.getLoopbackAddress(), port).apply { soTimeout = 5_000 }
        val reader = socket.getInputStream().bufferedReader(UTF_8)
        fun send(vararg lines: String) = socket.getOutputStream().run { write(lines.joinToString("\n", postfix = "\n").toByteArray(UTF_8)); flush() }
        override fun close() = socket.close()
    }

    @Test
    fun `over TCP, a request gets the best quote`() {
        val providers = listOf(northline(30), eastgate(60), fjord(10))
        QuoteService(Dispatchers.Default, BestQuote(providers, 2.seconds)).use { service ->
            val server = QuoteServer(1, service)
            try {
                assertThat(server.group()).isInstanceOf(MultiThreadIoEventLoopGroup::class.java)
                Client(server.port()).use { c ->
                    c.send("1 LISBON")
                    assertThat(c.reader.readLine()).isEqualTo("1 OK LISBON 12.41 eastgate")
                }
            } finally {
                server.close()
            }
        }
    }

    @Test
    fun `over TCP, a client that hangs up cancels the provider calls of its pending requests`() {
        val started = CountDownLatch(6)
        val stopped = CountDownLatch(6)
        val hanging = listOf("northline", "eastgate", "fjord").map { n ->
            object : Provider {
                override val name = n
                override suspend fun quote(destination: String): Quote {
                    started.countDown()
                    try { awaitCancellation() } finally { stopped.countDown() }
                }
            }
        }
        QuoteService(Dispatchers.Default, BestQuote(hanging, 60.seconds)).use { service ->
            val server = QuoteServer(1, service)
            try {
                val client = Client(server.port())
                client.send("1 LISBON", "2 DUBLIN")
                assertThat(started.await(5, TimeUnit.SECONDS)).`as`("6 provider calls started").isTrue()
                client.close()
                assertThat(stopped.await(5, TimeUnit.SECONDS)).`as`("6 provider calls cancelled after the hang-up").isTrue()
            } finally {
                server.close()
            }
        }
    }
}
