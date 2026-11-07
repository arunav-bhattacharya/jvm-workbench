package workbench.coroutines.l10

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
class SharedStateAndTestingTest {

    // ---- BalanceBook: a critical section across coroutines ----

    @Test
    fun `100 concurrent credits all land`() = runTest {
        val book = BalanceBook { amount, _ -> delay(50); amount * 100 } // 50 ms FX call, EUR to cents
        repeat(100) { launch { book.credit("acc-1", 1, "EUR") } }
        advanceUntilIdle()
        assertThat(book.balance("acc-1")).`as`("cents after 100 credits of 1 EUR").isEqualTo(10_000)
    }

    @Test
    fun `conversions overlap, and only the balance update is one at a time`() = runTest {
        val active = AtomicInteger()
        val peak = AtomicInteger()
        val book = BalanceBook { amount, _ ->
            peak.accumulateAndGet(active.incrementAndGet(), ::maxOf)
            delay(50)
            active.decrementAndGet()
            amount * 100
        }
        repeat(100) { launch { book.credit("acc-1", 1, "EUR") } }
        advanceUntilIdle()
        assertThat(peak.get()).`as`("FX calls in flight at once").isEqualTo(100)
        assertThat(currentTime).`as`("virtual ms for 100 credits").isEqualTo(50)
        assertThat(book.balance("acc-1")).isEqualTo(10_000)
    }

    // ---- retryWithBackoff, tested on virtual time ----

    @Test
    fun `succeeds on the third attempt after waiting 100 then 200 ms`() = runTest {
        val attempts = CopyOnWriteArrayList<Pair<Int, Long>>()
        val result = retryWithBackoff(times = 5, initialDelay = 100.milliseconds, maxDelay = 10.seconds) { attempt ->
            attempts += attempt to currentTime
            if (attempt < 3) throw IOException("issuer 503") else "approved"
        }
        assertThat(result).isEqualTo("approved")
        assertThat(attempts).`as`("(attempt, virtual ms)").containsExactly(1 to 0L, 2 to 100L, 3 to 300L)
    }

    @Test
    fun `gives up after the last attempt and rethrows its exception`() = runTest {
        val thrown = runCatching {
            retryWithBackoff<String>(times = 4, initialDelay = 100.milliseconds, maxDelay = 10.seconds) { attempt ->
                throw IOException("issuer 503 on attempt $attempt")
            }
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IOException::class.java).hasMessage("issuer 503 on attempt 4")
        assertThat(currentTime).`as`("virtual ms: 100 + 200 + 400").isEqualTo(700)
    }

    @Test
    fun `never waits longer than maxDelay`() = runTest {
        val attempts = CopyOnWriteArrayList<Long>()
        runCatching {
            retryWithBackoff<Unit>(times = 4, initialDelay = 1.seconds, maxDelay = 5.seconds, factor = 10.0) {
                attempts += currentTime
                throw IOException("down")
            }
        }
        assertThat(attempts).`as`("virtual ms of each attempt: waits of 1 s, 5 s, 5 s").containsExactly(0L, 1_000L, 6_000L, 11_000L)
    }

    @Test
    fun `does not retry an exception that retryOn rejects`() = runTest {
        val calls = AtomicInteger()
        val thrown = runCatching {
            retryWithBackoff<Unit>(times = 5, initialDelay = 100.milliseconds, maxDelay = 1.seconds) {
                calls.incrementAndGet()
                throw IllegalArgumentException("card number invalid")
            }
        }.exceptionOrNull()
        assertThat(thrown).isInstanceOf(IllegalArgumentException::class.java)
        assertThat(calls.get()).isEqualTo(1)
        assertThat(currentTime).isZero()
    }

    @Test
    fun `cancelling during a wait stops the retries`() = runTest {
        val calls = AtomicInteger()
        val job = launch {
            retryWithBackoff<Unit>(times = 10, initialDelay = 100.milliseconds, maxDelay = 10.seconds) {
                calls.incrementAndGet()
                throw IOException("down")
            }
        }
        advanceTimeBy(150) // attempt 1 at 0 ms, attempt 2 at 100 ms, now waiting until 300 ms
        job.cancel()
        advanceUntilIdle()
        assertThat(calls.get()).`as`("attempts made").isEqualTo(2)
        assertThat(job.isCancelled).isTrue()
    }
}
