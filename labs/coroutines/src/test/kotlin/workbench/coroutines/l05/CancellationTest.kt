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

    // ---- countStones: a CPU loop must check for cancellation ----

    @Test
    fun `countStones counts every stone when nobody cancels`() = runTest {
        val lentils = LongArray(10_000) { it.toLong() }
        assertThat(countStones(lentils) { it % 100 == 0L }).isEqualTo(100)
    }

    @Test
    fun `countStones stops within 1,000 lentils of being cancelled`() = runBlocking<Unit> {
        val lentils = LongArray(2_000_000) { it.toLong() }
        val calls = AtomicInteger()
        val reached = CountDownLatch(1)
        val cancelSent = CountDownLatch(1)
        val sorting = launch(Dispatchers.Default) {
            countStones(lentils) { lentil ->
                // pause at the 5,000th lentil until the test has cancelled the sorting
                if (calls.incrementAndGet() == 5_000) {
                    reached.countDown()
                    cancelSent.await(5, TimeUnit.SECONDS)
                }
                lentil % 97 == 0L
            }
        }
        assertThat(reached.await(5, TimeUnit.SECONDS)).isTrue()
        sorting.cancel()
        cancelSent.countDown()
        withTimeout(10.seconds) { sorting.join() }
        assertThat(calls.get()).`as`("lentils checked in total (cancelled at 5,000 of 2,000,000)").isLessThanOrEqualTo(6_001)
    }

    // ---- confirmEach: never swallow CancellationException ----

    @Test
    fun `confirmEach skips a failing call and reports it`() = runTest {
        val confirmed = CopyOnWriteArrayList<String>()
        val failed = confirmEach(listOf("o1", "bad", "o3")) { order ->
            delay(100)
            if (order == "bad") throw IOException("line busy")
            confirmed += order
        }
        assertThat(failed).containsExactly("bad")
        assertThat(confirmed).containsExactly("o1", "o3")
    }

    @Test
    fun `cancelling confirmEach stops the round at the call in progress`() = runTest {
        val started = CopyOnWriteArrayList<String>()
        var failed: List<String>? = null
        val round = launch {
            failed = confirmEach((1..20).map { "o$it" }) { order ->
                started += order
                delay(100) // the phone call to the supplier
            }
        }
        advanceTimeBy(250) // o1 and o2 are done, o3 is in progress
        round.cancelAndJoin()
        assertThat(started).`as`("calls started").containsExactly("o1", "o2", "o3")
        assertThat(failed).`as`("a cancelled round returns nothing").isNull()
        assertThat(round.isCancelled).isTrue()
    }

    // ---- withBorrowed: suspending cleanup needs NonCancellable ----

    private class FakeDesk : LendingDesk {
        val returned = CopyOnWriteArrayList<String>()
        override suspend fun lend(item: String): String { delay(20); return "ticket-$item" }
        override suspend fun giveBack(ticket: String) { delay(50); returned += ticket } // a phone call
    }

    @Test
    fun `withBorrowed gives the pot back when the block throws`() = runTest {
        val desk = FakeDesk()
        runCatching { withBorrowed(desk, "jam-pan") { delay(100); throw IOException("jam burned") } }
        assertThat(desk.returned).containsExactly("ticket-jam-pan")
    }

    @Test
    fun `withBorrowed gives the pot back when the caller is cancelled`() = runTest {
        val desk = FakeDesk()
        val jam = launch { withBorrowed(desk, "jam-pan") { delay(10_000) } }
        advanceTimeBy(1_000)
        jam.cancelAndJoin()
        assertThat(desk.returned).`as`("tickets given back").containsExactly("ticket-jam-pan")
        assertThat(currentTime).`as`("virtual ms: cancelled at 1,000, giving back took 50").isEqualTo(1_050)
    }

    // ---- askBakery: timeouts and blocking calls ----

    @Test
    fun `askBakery returns the answer when the bakery picks up in time`() = runBlocking<Unit> {
        // real time, not runTest: under runTest the timeout would run on virtual time and fire
        // while the test waits for the real IO thread (lesson 10 of this track explains why)
        assertThat(askBakery({ "two loaves left" }, "sourdough", 1.seconds)).isEqualTo("two loaves left")
    }

    @Test
    fun `askBakery returns null on timeout and interrupts the blocked call`() = runBlocking<Unit> {
        val interrupted = AtomicBoolean(false)
        val slowBakery = BakeryHotline {
            try {
                Thread.sleep(5_000) // a phone nobody picks up
                "two loaves left"
            } catch (e: InterruptedException) {
                interrupted.set(true)
                throw e
            }
        }
        val started = System.nanoTime()
        val answer = askBakery(slowBakery, "sourdough", 200.milliseconds)
        val tookMs = (System.nanoTime() - started) / 1_000_000
        assertThat(answer).isNull()
        assertThat(interrupted.get()).`as`("the blocked call was interrupted").isTrue()
        assertThat(tookMs).`as`("ms the caller waited (timeout 200, call 5,000)").isLessThan(3_000)
    }
}
