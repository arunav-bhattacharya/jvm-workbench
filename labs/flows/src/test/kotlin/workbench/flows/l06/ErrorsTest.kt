package workbench.flows.l06

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.FlowPreview
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.timeout
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.TestScope
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import kotlin.time.Duration.Companion.milliseconds

@OptIn(ExperimentalCoroutinesApi::class, FlowPreview::class) // currentTime & co. in kotlinx-coroutines-test 1.11.0; timeout()
class ErrorsTest {

    /** Collects [flow] and returns the virtual time and either the values or the exception. */
    private suspend fun <T> TestScope.outcome(flow: Flow<T>): Triple<Long, List<T>, Throwable?> {
        val values = mutableListOf<T>()
        val failure = runCatching { flow.collect { values += it } }.exceptionOrNull()
        return Triple(currentTime, values, failure)
    }

    // ---- retryWithBackoff ----

    @Test
    fun `retryWithBackoff collects at 0, 100, 300 and 700 ms, then lets the original error out`() = runTest {
        val calls = mutableListOf<Long>()
        var n = 0
        val alwaysFails = flow<Int> { calls += currentTime; n++; throw IOException("PSP reset (call $n)") }
        val (_, _, failure) = outcome(alwaysFails.retryWithBackoff())
        assertThat(calls).`as`("virtual ms of each collection").containsExactly(0L, 100L, 300L, 700L)
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("PSP reset (call 4)")
    }

    @Test
    fun `retryWithBackoff caps the wait at max`() = runTest {
        val calls = mutableListOf<Long>()
        val alwaysFails = flow<Int> { calls += currentTime; throw IOException("down") }
        outcome(alwaysFails.retryWithBackoff(maxRetries = 3, first = 300.milliseconds, max = 500.milliseconds))
        assertThat(calls).`as`("waits of 300, then 600 and 1200 capped to 500").containsExactly(0L, 300L, 800L, 1300L)
    }

    @Test
    fun `retryWithBackoff does not retry an error that retryOn rejects`() = runTest {
        var n = 0
        val declined = flow<Int> { n++; throw IllegalArgumentException("card declined") }
        val (time, _, failure) = outcome(declined.retryWithBackoff())
        assertThat(n).`as`("collections").isEqualTo(1)
        assertThat(time).isEqualTo(0)
        assertThat(failure).isInstanceOf(IllegalArgumentException::class.java).hasMessage("card declined")
    }

    @Test
    fun `a timeout from timeout() counts as transient and is retried`() = runTest {
        val calls = mutableListOf<Long>()
        val slow = flow { calls += currentTime; delay(1_000); emit(1) }
        val (time, _, failure) = outcome(slow.timeout(300.milliseconds).retryWithBackoff())
        assertThat(calls).containsExactly(0L, 400L, 900L, 1600L)
        assertThat(failure).isInstanceOf(TimeoutCancellationException::class.java)
        assertThat(time).isEqualTo(1900)
    }

    // ---- fxRate: per-attempt timeout, retry with backoff, then a fallback ----

    /** A fake provider: [script] says what call n does: a latency in ms, or an exception to throw after 20 ms. */
    private class FakeProvider(private val name: String, private val script: (call: Int) -> Any) : RateProvider {
        var calls = 0
        override fun rate(pair: String): Flow<Rate> = flow {
            val n = ++calls
            when (val step = script(n)) {
                is Long -> { delay(step); emit(Rate(pair, 0.92, name)) }
                is Throwable -> { delay(20); throw step }
                else -> error("bad script")
            }
        }
    }

    @Test
    fun `fxRate retries two resets and answers from the primary at 390 ms`() = runTest {
        val primary = FakeProvider("primary") { n -> if (n <= 2) IOException("connection reset") else 50L }
        val fallback = FakeProvider("fallback") { 30L }
        val (time, values, failure) = outcome(fxRate("USD/EUR", primary, fallback))
        assertThat(failure).isNull()
        assertThat(values).containsExactly(Rate("USD/EUR", 0.92, "primary"))
        assertThat(time).`as`("calls at 0, 120 and 340; the third answers in 50 ms").isEqualTo(390)
        assertThat(primary.calls to fallback.calls).isEqualTo(3 to 0)
    }

    @Test
    fun `fxRate cuts each slow call at 300 ms, retries, then falls back at 1900 ms`() = runTest {
        val primary = FakeProvider("primary") { 1_000L }
        val fallback = FakeProvider("fallback") { 30L }
        val (time, values, failure) = outcome(fxRate("USD/EUR", primary, fallback))
        assertThat(failure).isNull()
        assertThat(values).containsExactly(Rate("USD/EUR", 0.92, "fallback"))
        assertThat(time).`as`("calls at 0, 400, 900, 1600, each cut at +300; fallback answers in 30 ms").isEqualTo(1930)
        assertThat(primary.calls to fallback.calls).isEqualTo(4 to 1)
    }

    @Test
    fun `fxRate passes a non-transient error straight to the caller`() = runTest {
        val primary = FakeProvider("primary") { IllegalArgumentException("unsupported pair XXX/EUR") }
        val fallback = FakeProvider("fallback") { 30L }
        val (time, _, failure) = outcome(fxRate("XXX/EUR", primary, fallback))
        assertThat(failure).isInstanceOf(IllegalArgumentException::class.java).hasMessage("unsupported pair XXX/EUR")
        assertThat(time).isEqualTo(20)
        assertThat(primary.calls to fallback.calls).isEqualTo(1 to 0)
    }

    @Test
    fun `fxRate reports the fallback's failure when both providers are down`() = runTest {
        val primary = FakeProvider("primary") { IOException("primary down") }
        val fallback = FakeProvider("fallback") { IOException("fallback down") }
        val (time, _, failure) = outcome(fxRate("USD/EUR", primary, fallback))
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("fallback down")
        assertThat(time).isEqualTo(800)
        assertThat(primary.calls to fallback.calls).isEqualTo(4 to 1)
    }

    @Test
    fun `a cancelled caller stops fxRate with no retry and no fallback`() = runTest {
        val primary = FakeProvider("primary") { 1_000L }
        val fallback = FakeProvider("fallback") { 30L }
        var ended: Throwable? = null
        val caller = launch {
            try { fxRate("USD/EUR", primary, fallback).collect { } } catch (e: Throwable) { ended = e; throw e }
        }
        advanceTimeBy(150); runCurrent()
        caller.cancel()                         // the HTTP request that wanted the rate went away
        advanceUntilIdle()
        assertThat(caller.isCancelled).isTrue()
        assertThat(ended).isInstanceOf(CancellationException::class.java)
        assertThat(primary.calls to fallback.calls).`as`("(primary calls, fallback calls)").isEqualTo(1 to 0)
    }

    // ---- uniquePayments: retry replays ----

    /** Emits payment-1..3, 10 ms apart. The first collection fails with an IOException before payment-3. */
    private fun flakyFeed(): Flow<Payment> {
        var collections = 0
        return flow {
            collections++
            for (i in 1..3) {
                delay(10)
                if (collections == 1 && i == 3) throw IOException("stream reset")
                emit(Payment("payment-$i", 100L * i))
            }
        }
    }

    @Test
    fun `uniquePayments delivers each payment once even though the retry replays the feed`() = runTest {
        val ids = uniquePayments(flakyFeed()).toList().map { it.id }
        assertThat(ids).containsExactly("payment-1", "payment-2", "payment-3")
    }

    @Test
    fun `uniquePayments starts fresh on every collection`() = runTest {
        val payments = uniquePayments(flowOfThree())
        assertThat(payments.toList().map { it.id }).containsExactly("payment-1", "payment-2", "payment-3")
        assertThat(payments.toList().map { it.id }).`as`("second collection of the same flow")
            .containsExactly("payment-1", "payment-2", "payment-3")
    }

    private fun flowOfThree(): Flow<Payment> = flow { for (i in 1..3) emit(Payment("payment-$i", 100L * i)) }

    @Test
    fun `uniquePayments still fails when the feed keeps failing`() = runTest {
        val dead = flow<Payment> { throw IOException("feed down") }
        val (_, _, failure) = outcome(uniquePayments(dead))
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("feed down")
        assertThat(currentTime).`as`("three backoff waits: 100 + 200 + 400").isEqualTo(700)
    }
}
