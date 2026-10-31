package workbench.coroutines.l03

import kotlinx.coroutines.CancellationException
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.io.IOException
import java.util.concurrent.CopyOnWriteArrayList

@OptIn(ExperimentalCoroutinesApi::class)
class StructuredConcurrencyTest {

    // ---- settleAll ----

    @Test
    fun `settleAll returns only after every batch is settled`() = runTest {
        val settled = CopyOnWriteArrayList<String>()
        settleAll(listOf("b1", "b2", "b3")) { id -> delay(100L * id.last().digitToInt()); settled += id }
        assertThat(settled).`as`("settled when settleAll returned").containsExactlyInAnyOrder("b1", "b2", "b3")
        assertThat(currentTime).`as`("virtual ms: the slowest batch").isEqualTo(300)
    }

    @Test
    fun `a failing batch cancels the others and the caller gets the failure`() = runTest {
        val cancelled = CopyOnWriteArrayList<String>()
        var thrown: Throwable? = null
        try {
            settleAll(listOf("ok-1", "bad", "ok-2")) { id ->
                if (id == "bad") { delay(50); throw IOException("issuer file rejected") }
                try { delay(1_000) } catch (e: CancellationException) { cancelled += id; throw e }
            }
        } catch (e: IOException) {
            thrown = e
        }
        assertThat(thrown).hasMessage("issuer file rejected")
        assertThat(cancelled).containsExactlyInAnyOrder("ok-1", "ok-2")
        assertThat(currentTime).`as`("failed at the failure, not after the slow batches").isEqualTo(50)
    }

    @Test
    fun `cancelling the caller cancels every batch`() = runTest {
        val finished = CopyOnWriteArrayList<String>()
        val caller = launch { settleAll(listOf("b1", "b2")) { id -> delay(1_000); finished += id } }
        advanceTimeBy(100)
        caller.cancelAndJoin()
        advanceUntilIdle()
        assertThat(finished).`as`("batches that kept running after the caller left").isEmpty()
    }

    // ---- BatchSettler ----

    @Test
    fun `submit starts the batch in the background and returns at once`() = runTest {
        val settled = CopyOnWriteArrayList<String>()
        val settler = BatchSettler(StandardTestDispatcher(testScheduler)) { id -> delay(500); settled += id }
        settler.submit("b1")
        assertThat(settled).isEmpty()
        advanceUntilIdle()
        assertThat(settled).containsExactly("b1")
    }

    @Test
    fun `inFlight counts the batches still running`() = runTest {
        val settler = BatchSettler(StandardTestDispatcher(testScheduler)) { id -> delay(100L * id.last().digitToInt()) }
        listOf("b1", "b2", "b3").forEach { settler.submit(it) }
        runCurrent()
        assertThat(settler.inFlight).isEqualTo(3)
        advanceTimeBy(150); runCurrent()
        assertThat(settler.inFlight).isEqualTo(2)
        advanceUntilIdle()
        assertThat(settler.inFlight).isEqualTo(0)
    }

    @Test
    fun `shutdown cancels running batches and waits until they have stopped`() = runTest {
        val settled = CopyOnWriteArrayList<String>()
        val stopped = CopyOnWriteArrayList<String>()
        val settler = BatchSettler(StandardTestDispatcher(testScheduler)) { id ->
            try { delay(10_000); settled += id } finally { stopped += id }
        }
        settler.submit("b1"); settler.submit("b2")
        runCurrent()

        settler.shutdown()

        assertThat(stopped).`as`("stopped when shutdown returned").containsExactlyInAnyOrder("b1", "b2")
        assertThat(settled).isEmpty()
        assertThat(currentTime).isEqualTo(0)
    }

    @Test
    fun `submit after shutdown is refused`() = runTest {
        val settler = BatchSettler(StandardTestDispatcher(testScheduler)) { delay(10) }
        settler.shutdown()
        assertThatThrownBy { settler.submit("late") }.isInstanceOf(IllegalStateException::class.java)
    }
}
