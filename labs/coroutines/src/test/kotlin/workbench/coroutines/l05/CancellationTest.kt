package workbench.coroutines.l05

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import kotlinx.coroutines.withTimeout
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import kotlin.time.Duration.Companion.milliseconds
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
class CancellationTest {

    // ---- countFlagged: a CPU loop must check for cancellation ----

    @Test
    fun `countFlagged counts every flagged amount when nobody cancels`() = runTest {
        val amounts = LongArray(10_000) { it.toLong() }
        assertThat(countFlagged(amounts) { it % 100 == 0L }).isEqualTo(100)
    }

    @Test
    fun `countFlagged stops within 1,000 amounts of being cancelled`() = runBlocking<Unit> {
        val amounts = LongArray(2_000_000) { it.toLong() }
        val calls = AtomicInteger()
        val reached = CountDownLatch(1)
        val cancelSent = CountDownLatch(1)
        val scan = launch(Dispatchers.Default) {
            countFlagged(amounts) { amount ->
                // pause at the 5,000th amount until the test has cancelled the scan
                if (calls.incrementAndGet() == 5_000) {
                    reached.countDown()
                    cancelSent.await(5, TimeUnit.SECONDS)
                }
                amount % 97 == 0L
            }
        }
        assertThat(reached.await(5, TimeUnit.SECONDS)).isTrue()
        scan.cancel()
        cancelSent.countDown()
        withTimeout(10.seconds) { scan.join() }
        assertThat(calls.get()).`as`("amounts checked in total (cancelled at 5,000 of 2,000,000)").isLessThanOrEqualTo(6_001)
    }

    // ---- settleEach: never swallow CancellationException ----

    @Test
    fun `settleEach skips a failing batch and reports it`() = runTest {
        val settled = CopyOnWriteArrayList<String>()
        val failed = settleEach(listOf("b1", "bad", "b3")) { id ->
            delay(100)
            if (id == "bad") throw IOException("acquirer rejected file")
            settled += id
        }
        assertThat(failed).containsExactly("bad")
        assertThat(settled).containsExactly("b1", "b3")
    }

    @Test
    fun `cancelling settleEach stops the run at the batch in progress`() = runTest {
        val started = CopyOnWriteArrayList<String>()
        var failed: List<String>? = null
        val run = launch {
            failed = settleEach((1..20).map { "b$it" }) { id ->
                started += id
                delay(100) // the acquirer call
            }
        }
        advanceTimeBy(250) // b1 and b2 are done, b3 is in progress
        run.cancelAndJoin()
        assertThat(started).`as`("batches started").containsExactly("b1", "b2", "b3")
        assertThat(failed).`as`("a cancelled run returns nothing").isNull()
        assertThat(run.isCancelled).isTrue()
    }

    // ---- withCardHold: suspending cleanup needs NonCancellable ----

    private class FakeHolds : HoldApi {
        val released = CopyOnWriteArrayList<String>()
        override suspend fun place(amountCents: Long): String { delay(20); return "hold-$amountCents" }
        override suspend fun release(holdId: String) { delay(50); released += holdId } // a network call
    }

    @Test
    fun `withCardHold releases the hold when the block throws`() = runTest {
        val holds = FakeHolds()
        runCatching { withCardHold(holds, 4_250) { delay(100); throw IOException("issuer timeout") } }
        assertThat(holds.released).containsExactly("hold-4250")
    }

    @Test
    fun `withCardHold releases the hold when the caller is cancelled`() = runTest {
        val holds = FakeHolds()
        val payment = launch { withCardHold(holds, 4_250) { delay(10_000) } }
        advanceTimeBy(1_000)
        payment.cancelAndJoin()
        assertThat(holds.released).`as`("holds released").containsExactly("hold-4250")
        assertThat(currentTime).`as`("virtual ms: cancelled at 1,000, release took 50").isEqualTo(1_050)
    }

    // ---- lookupBrand: timeouts and blocking calls ----

    @Test
    fun `lookupBrand returns the brand when the directory answers in time`() = runBlocking<Unit> {
        // real time, not runTest: under runTest the timeout would run on virtual time and fire
        // while the test waits for the real IO thread (lesson 10 of this track explains why)
        assertThat(lookupBrand({ "VISA DEBIT" }, "412345", 1.seconds)).isEqualTo("VISA DEBIT")
    }

    @Test
    fun `lookupBrand returns null on timeout and interrupts the blocked call`() = runBlocking<Unit> {
        val interrupted = AtomicBoolean(false)
        val slowDirectory = BinDirectory {
            try {
                Thread.sleep(5_000) // a hung legacy service
                "VISA DEBIT"
            } catch (e: InterruptedException) {
                interrupted.set(true)
                throw e
            }
        }
        val started = System.nanoTime()
        val brand = lookupBrand(slowDirectory, "412345", 200.milliseconds)
        val tookMs = (System.nanoTime() - started) / 1_000_000
        assertThat(brand).isNull()
        assertThat(interrupted.get()).`as`("the blocked lookup was interrupted").isTrue()
        assertThat(tookMs).`as`("ms the caller waited (timeout 200, lookup 5,000)").isLessThan(3_000)
    }
}
