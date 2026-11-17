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
import java.util.concurrent.CopyOnWriteArrayList

/** A dish that went wrong. (Not an IllegalStateException: CancellationException is one of those.) */
private class BurnedException(message: String) : Exception(message)

@OptIn(ExperimentalCoroutinesApi::class)
class StructuredConcurrencyTest {

    // ---- cookCourse ----

    @Test
    fun `cookCourse returns only after every dish is done`() = runTest {
        val done = CopyOnWriteArrayList<String>()
        cookCourse(listOf("dish1", "dish2", "dish3")) { d -> delay(100L * d.last().digitToInt()); done += d }
        assertThat(done).`as`("done when cookCourse returned").containsExactlyInAnyOrder("dish1", "dish2", "dish3")
        assertThat(currentTime).`as`("virtual ms: the slowest dish").isEqualTo(300)
    }

    @Test
    fun `a failing dish cancels the others and the caller gets the failure`() = runTest {
        val cancelled = CopyOnWriteArrayList<String>()
        var thrown: Throwable? = null
        try {
            cookCourse(listOf("potatoes", "roast", "gravy")) { d ->
                if (d == "roast") { delay(50); throw BurnedException("the roast burned") }
                try { delay(1_000) } catch (e: CancellationException) { cancelled += d; throw e }
            }
        } catch (e: BurnedException) {
            thrown = e
        }
        assertThat(thrown).hasMessage("the roast burned")
        assertThat(cancelled).containsExactlyInAnyOrder("potatoes", "gravy")
        assertThat(currentTime).`as`("failed at the failure, not after the slow dishes").isEqualTo(50)
    }

    @Test
    fun `cancelling the caller cancels every dish`() = runTest {
        val finished = CopyOnWriteArrayList<String>()
        val caller = launch { cookCourse(listOf("soup", "bread")) { d -> delay(1_000); finished += d } }
        advanceTimeBy(100)
        caller.cancelAndJoin()
        advanceUntilIdle()
        assertThat(finished).`as`("dishes that kept cooking after the caller left").isEmpty()
    }

    // ---- Oven ----

    @Test
    fun `put starts baking in the background and returns at once`() = runTest {
        val baked = CopyOnWriteArrayList<String>()
        val oven = Oven(StandardTestDispatcher(testScheduler)) { tray -> delay(500); baked += tray }
        oven.put("tray1")
        assertThat(baked).isEmpty()
        advanceUntilIdle()
        assertThat(baked).containsExactly("tray1")
    }

    @Test
    fun `inOven counts the trays still baking`() = runTest {
        val oven = Oven(StandardTestDispatcher(testScheduler)) { tray -> delay(100L * tray.last().digitToInt()) }
        listOf("tray1", "tray2", "tray3").forEach { oven.put(it) }
        runCurrent()
        assertThat(oven.inOven).isEqualTo(3)
        advanceTimeBy(150); runCurrent()
        assertThat(oven.inOven).isEqualTo(2)
        advanceUntilIdle()
        assertThat(oven.inOven).isEqualTo(0)
    }

    @Test
    fun `switchOff cancels the trays and waits until they have stopped`() = runTest {
        val baked = CopyOnWriteArrayList<String>()
        val stopped = CopyOnWriteArrayList<String>()
        val oven = Oven(StandardTestDispatcher(testScheduler)) { tray ->
            try { delay(10_000); baked += tray } finally { stopped += tray }
        }
        oven.put("tray1"); oven.put("tray2")
        runCurrent()

        oven.switchOff()

        assertThat(stopped).`as`("stopped when switchOff returned").containsExactlyInAnyOrder("tray1", "tray2")
        assertThat(baked).isEmpty()
        assertThat(currentTime).isEqualTo(0)
    }

    @Test
    fun `a tray put in after switchOff is refused`() = runTest {
        val oven = Oven(StandardTestDispatcher(testScheduler)) { delay(10) }
        oven.switchOff()
        assertThatThrownBy { oven.put("late") }.isInstanceOf(IllegalStateException::class.java)
    }
}
