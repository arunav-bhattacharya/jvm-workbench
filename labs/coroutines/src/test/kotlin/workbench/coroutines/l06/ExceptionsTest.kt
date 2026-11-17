package workbench.coroutines.l06

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.StandardTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList
import kotlin.time.Duration.Companion.seconds

@OptIn(ExperimentalCoroutinesApi::class)
class ExceptionsTest {

    // ---- bakeAll: every tray of one order, inside the caller's call ----

    @Test
    fun `bakeAll bakes every tray when nothing burns`() = runTest {
        val baked = CopyOnWriteArrayList<Tray>()
        val bakers = Tray.entries.associateWith { tray -> Baker { delay(100); baked += tray } }
        val outcomes = bakeAll("order-1", bakers, 2.seconds)
        assertThat(outcomes).containsOnlyKeys(*Tray.entries.toTypedArray())
        assertThat(outcomes.values).containsOnly(Outcome.Baked)
        assertThat(currentTime).`as`("virtual ms: baked at the same time").isEqualTo(100)
    }

    @Test
    fun `one burned tray does not stop the others`() = runTest {
        val baked = CopyOnWriteArrayList<Tray>()
        val bakers = mapOf(
            Tray.COOKIES to Baker { delay(300); baked += Tray.COOKIES },
            Tray.SCONES to Baker { delay(50); throw BurnedException("the scones burned") },
            Tray.MUFFINS to Baker { delay(100); baked += Tray.MUFFINS },
        )
        val outcomes = bakeAll("order-1", bakers, 2.seconds)
        assertThat(outcomes).isEqualTo(
            mapOf(Tray.COOKIES to Outcome.Baked, Tray.SCONES to Outcome.Failed("the scones burned"), Tray.MUFFINS to Outcome.Baked)
        )
        assertThat(baked).containsExactlyInAnyOrder(Tray.COOKIES, Tray.MUFFINS)
        assertThat(currentTime).isEqualTo(300)
    }

    @Test
    fun `a tray slower than the timeout counts as failed`() = runTest {
        val bakers = mapOf(
            Tray.COOKIES to Baker { delay(100) },
            Tray.SCONES to Baker { delay(10_000) }, // an oven that never gets hot
        )
        val outcomes = bakeAll("order-1", bakers, 2.seconds)
        assertThat(outcomes).isEqualTo(mapOf(Tray.COOKIES to Outcome.Baked, Tray.SCONES to Outcome.Failed("timed out")))
        assertThat(currentTime).`as`("virtual ms: gave up on the scones at the timeout").isEqualTo(2_000)
    }

    @Test
    fun `cancelling the caller cancels every tray`() = runTest {
        val baked = CopyOnWriteArrayList<Tray>()
        var outcomes: Map<Tray, Outcome>? = null
        val caller = launch {
            outcomes = bakeAll("order-1", Tray.entries.associateWith { tray -> Baker { delay(1_000); baked += tray } }, 5.seconds)
        }
        advanceTimeBy(500)
        caller.cancelAndJoin()
        advanceUntilIdle()
        assertThat(baked).`as`("trays that finished after the caller left").isEmpty()
        assertThat(outcomes).`as`("a cancelled call returns no outcomes").isNull()
    }

    // ---- Oven: background work that outlives the call that started it ----

    private class Recorder {
        val burned = CopyOnWriteArrayList<String>()
        val baked = CopyOnWriteArrayList<String>()
    }

    @Test
    fun `a burned tray does not cancel the others`() = runTest {
        val r = Recorder()
        val oven = Oven(StandardTestDispatcher(testScheduler)) { tray, e -> r.burned += "$tray: ${e.message}" }
        oven.put("tray-1") { delay(100); throw BurnedException("black at the edges") }
        oven.put("tray-2") { delay(300); r.baked += it }
        advanceUntilIdle()
        assertThat(r.baked).containsExactly("tray-2")
        oven.switchOff()
    }

    @Test
    fun `a failure is reported with the name of its tray`() = runTest {
        val r = Recorder()
        val oven = Oven(StandardTestDispatcher(testScheduler)) { tray, e -> r.burned += "$tray: ${e.message}" }
        oven.put("tray-7") { delay(10); throw BurnedException("black at the edges") }
        advanceUntilIdle()
        assertThat(r.burned).containsExactly("tray-7: black at the edges")
        oven.switchOff()
    }

    @Test
    fun `the oven keeps baking after a failure`() = runTest {
        val r = Recorder()
        val oven = Oven(StandardTestDispatcher(testScheduler)) { tray, e -> r.burned += "$tray: ${e.message}" }
        oven.put("tray-1") { throw BurnedException("black at the edges") }
        advanceUntilIdle()
        oven.put("tray-2") { delay(10); r.baked += it }
        advanceUntilIdle()
        assertThat(r.baked).`as`("trays baked after the failure").containsExactly("tray-2")
        oven.switchOff()
    }

    @Test
    fun `switchOff cancels the trays still baking and waits for them`() = runTest {
        val r = Recorder()
        val cleanedUp = CopyOnWriteArrayList<String>()
        val oven = Oven(StandardTestDispatcher(testScheduler)) { tray, e -> r.burned += "$tray: ${e.message}" }
        oven.put("tray-1") { tray -> try { delay(10_000); r.baked += tray } finally { cleanedUp += tray } }
        advanceTimeBy(100)
        assertThat(oven.inOven).`as`("trays in the oven before switchOff").isEqualTo(1)
        oven.switchOff()
        assertThat(cleanedUp).`as`("cleaned up when switchOff returned").containsExactly("tray-1")
        assertThat(r.baked).isEmpty()
        assertThat(oven.inOven).`as`("trays in the oven after switchOff").isEqualTo(0)
        assertThat(r.burned).`as`("a cancel is not a failure").isEmpty()
    }
}
