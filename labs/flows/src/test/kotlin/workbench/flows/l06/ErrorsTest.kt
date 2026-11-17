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
        val alwaysFails = flow<Int> { calls += currentTime; n++; throw IOException("line dropped (call $n)") }
        val (_, _, failure) = outcome(alwaysFails.retryWithBackoff())
        assertThat(calls).`as`("virtual ms of each collection").containsExactly(0L, 100L, 300L, 700L)
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("line dropped (call 4)")
    }

    @Test
    fun `retryWithBackoff caps the wait at max`() = runTest {
        val calls = mutableListOf<Long>()
        val alwaysFails = flow<Int> { calls += currentTime; throw IOException("no answer") }
        outcome(alwaysFails.retryWithBackoff(maxRetries = 3, first = 300.milliseconds, max = 500.milliseconds))
        assertThat(calls).`as`("waits of 300, then 600 and 1200 capped to 500").containsExactly(0L, 300L, 800L, 1300L)
    }

    @Test
    fun `retryWithBackoff does not retry an error that retryOn rejects`() = runTest {
        var n = 0
        val declined = flow<Int> { n++; throw IllegalArgumentException("nobody bakes that") }
        val (time, _, failure) = outcome(declined.retryWithBackoff())
        assertThat(n).`as`("collections").isEqualTo(1)
        assertThat(time).isEqualTo(0)
        assertThat(failure).isInstanceOf(IllegalArgumentException::class.java).hasMessage("nobody bakes that")
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

    // ---- freshLoaf: per-attempt timeout, retry with backoff, then the backup bakery ----

    /** A fake bakery: [script] says what call n does: a latency in ms, or an exception to throw after 20 ms. */
    private class FakeBakery(private val name: String, private val script: (call: Int) -> Any) : Bakery {
        var calls = 0
        override fun order(kind: String): Flow<Loaf> = flow {
            val n = ++calls
            when (val step = script(n)) {
                is Long -> { delay(step); emit(Loaf(kind, name)) }
                is Throwable -> { delay(20); throw step }
                else -> error("bad script")
            }
        }
    }

    @Test
    fun `freshLoaf retries two dropped calls and gets the loaf from the bakery at 390 ms`() = runTest {
        val bakery = FakeBakery("corner") { n -> if (n <= 2) IOException("line dropped") else 50L }
        val backup = FakeBakery("backup") { 30L }
        val (time, values, failure) = outcome(freshLoaf("sourdough", bakery, backup))
        assertThat(failure).isNull()
        assertThat(values).containsExactly(Loaf("sourdough", "corner"))
        assertThat(time).`as`("calls at 0, 120 and 340; the third answers in 50 ms").isEqualTo(390)
        assertThat(bakery.calls to backup.calls).isEqualTo(3 to 0)
    }

    @Test
    fun `freshLoaf cuts each slow call at 300 ms, retries, then asks the backup at 1900 ms`() = runTest {
        val bakery = FakeBakery("corner") { 1_000L }
        val backup = FakeBakery("backup") { 30L }
        val (time, values, failure) = outcome(freshLoaf("sourdough", bakery, backup))
        assertThat(failure).isNull()
        assertThat(values).containsExactly(Loaf("sourdough", "backup"))
        assertThat(time).`as`("calls at 0, 400, 900, 1600, each cut at +300; the backup answers in 30 ms").isEqualTo(1930)
        assertThat(bakery.calls to backup.calls).isEqualTo(4 to 1)
    }

    @Test
    fun `freshLoaf passes an error that is not transient straight to the caller`() = runTest {
        val bakery = FakeBakery("corner") { IllegalArgumentException("nobody bakes moon bread") }
        val backup = FakeBakery("backup") { 30L }
        val (time, _, failure) = outcome(freshLoaf("moon bread", bakery, backup))
        assertThat(failure).isInstanceOf(IllegalArgumentException::class.java).hasMessage("nobody bakes moon bread")
        assertThat(time).isEqualTo(20)
        assertThat(bakery.calls to backup.calls).isEqualTo(1 to 0)
    }

    @Test
    fun `freshLoaf reports the backup's failure when both bakeries are closed`() = runTest {
        val bakery = FakeBakery("corner") { IOException("corner bakery closed") }
        val backup = FakeBakery("backup") { IOException("backup bakery closed") }
        val (time, _, failure) = outcome(freshLoaf("sourdough", bakery, backup))
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("backup bakery closed")
        assertThat(time).isEqualTo(800)
        assertThat(bakery.calls to backup.calls).isEqualTo(4 to 1)
    }

    @Test
    fun `a cancelled caller stops freshLoaf with no retry and no backup`() = runTest {
        val bakery = FakeBakery("corner") { 1_000L }
        val backup = FakeBakery("backup") { 30L }
        var ended: Throwable? = null
        val caller = launch {
            try { freshLoaf("sourdough", bakery, backup).collect { } } catch (e: Throwable) { ended = e; throw e }
        }
        advanceTimeBy(150); runCurrent()
        caller.cancel()                         // the diner who wanted the bread went home
        advanceUntilIdle()
        assertThat(caller.isCancelled).isTrue()
        assertThat(ended).isInstanceOf(CancellationException::class.java)
        assertThat(bakery.calls to backup.calls).`as`("(bakery calls, backup calls)").isEqualTo(1 to 0)
    }

    // ---- eachLineOnce: a retry reads the note again ----

    private val items = listOf("flour", "eggs", "butter")

    /** Emits line-1..3, 10 ms apart. The first collection fails with an IOException before line-3. */
    private fun flakyNote(): Flow<NoteLine> {
        var collections = 0
        return flow {
            collections++
            for (i in 1..3) {
                delay(10)
                if (collections == 1 && i == 3) throw IOException("the reader lost the connection")
                emit(NoteLine("line-$i", items[i - 1]))
            }
        }
    }

    @Test
    fun `eachLineOnce delivers each line once even though the retry reads the note again`() = runTest {
        val ids = eachLineOnce(flakyNote()).toList().map { it.id }
        assertThat(ids).containsExactly("line-1", "line-2", "line-3")
    }

    @Test
    fun `eachLineOnce starts fresh on every collection`() = runTest {
        val lines = eachLineOnce(noteOfThree())
        assertThat(lines.toList().map { it.id }).containsExactly("line-1", "line-2", "line-3")
        assertThat(lines.toList().map { it.id }).`as`("second collection of the same flow")
            .containsExactly("line-1", "line-2", "line-3")
    }

    private fun noteOfThree(): Flow<NoteLine> = flow { for (i in 1..3) emit(NoteLine("line-$i", items[i - 1])) }

    @Test
    fun `eachLineOnce still fails when the note can't be read at all`() = runTest {
        val dead = flow<NoteLine> { throw IOException("note unreadable") }
        val (_, _, failure) = outcome(eachLineOnce(dead))
        assertThat(failure).isInstanceOf(IOException::class.java).hasMessage("note unreadable")
        assertThat(currentTime).`as`("three backoff waits: 100 + 200 + 400").isEqualTo(700)
    }
}
