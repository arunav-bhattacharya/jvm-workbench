package workbench.coroutines.l08

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.delay
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.onCompletion
import kotlinx.coroutines.flow.onStart
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.UnconfinedTestDispatcher
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CyclicBarrier
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread
import workbench.coroutines.l08.DishStatus.CLEARED
import workbench.coroutines.l08.DishStatus.COOKING
import workbench.coroutines.l08.DishStatus.SERVED
import workbench.coroutines.l08.DishStatus.WAITING

@OptIn(ExperimentalCoroutinesApi::class)
class HotFlowsTest {

    // ---- DishTracker.status ----

    @Test
    fun `status starts as WAITING and follows allowed moves only`() {
        val t = DishTracker("soup")
        assertThat(t.status.value).isEqualTo(WAITING)
        assertThat(t.moveTo(SERVED)).`as`("WAITING -> SERVED is not allowed").isFalse()
        assertThat(t.moveTo(COOKING)).isTrue()
        assertThat(t.moveTo(COOKING)).`as`("moving to the same status").isFalse()
        assertThat(t.moveTo(SERVED)).isTrue()
        assertThat(t.status.value).isEqualTo(SERVED)
    }

    @Test
    fun `when two helpers serve the same dish, exactly one wins`() {
        // the hook holds each thread until both have passed the status check, so the two
        // moves always overlap (a real check would take a few ms and overlap by chance)
        val bothChecked = CyclicBarrier(2)
        val t = DishTracker("soup") { tr -> if (tr.to == SERVED) runCatching { bothChecked.await(2, TimeUnit.SECONDS) } }
        t.moveTo(COOKING)
        val results = CopyOnWriteArrayList<Boolean>()
        val helpers = List(2) { thread { results += t.moveTo(SERVED) } }
        helpers.forEach { it.join() }
        assertThat(results).`as`("what the two moveTo(SERVED) calls returned").containsExactlyInAnyOrder(true, false)
        assertThat(t.status.value).isEqualTo(SERVED)
    }

    // ---- DishTracker.transitions ----

    @Test
    fun `a busy kitchen log still receives every transition`() = runTest {
        val t = DishTracker("soup")
        val logged = CopyOnWriteArrayList<Transition>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
            t.transitions.collect { delay(100); logged += it } // writing a line in the log takes 100 ms
        }
        t.moveTo(COOKING)
        t.moveTo(SERVED)
        t.moveTo(CLEARED)
        advanceTimeBy(1_000) // not advanceUntilIdle: it doesn't wait for work in backgroundScope
        assertThat(logged).containsExactly(
            Transition("soup", WAITING, COOKING), Transition("soup", COOKING, SERVED), Transition("soup", SERVED, CLEARED),
        )
    }

    @Test
    fun `a late subscriber sees only transitions after it subscribed`() = runTest {
        val t = DishTracker("soup")
        t.moveTo(COOKING) // nobody is listening yet
        val logged = CopyOnWriteArrayList<Transition>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { t.transitions.collect { logged += it } }
        t.moveTo(SERVED)
        runCurrent()
        assertThat(logged).containsExactly(Transition("soup", COOKING, SERVED))
    }

    // ---- liveServedCount: stateIn with WhileSubscribed ----

    private class Upstream {
        val starts = AtomicInteger()
        val stops = AtomicInteger()
        fun servings(vararg plates: Int): Flow<Int> = flow {
            for (p in plates) { delay(100); emit(p) }
            delay(Long.MAX_VALUE) // a live feed never ends on its own
        }.onStart { starts.incrementAndGet() }.onCompletion { stops.incrementAndGet() }
    }

    @Test
    fun `the count does not collect until a screen subscribes`() = runTest {
        val up = Upstream()
        val count = liveServedCount(up.servings(4, 2), backgroundScope)
        runCurrent()
        assertThat(up.starts.get()).`as`("upstream starts before anyone subscribed").isZero()
        assertThat(count.value).isZero()

        backgroundScope.launch { count.collect { } }
        advanceTimeBy(250)
        assertThat(up.starts.get()).isEqualTo(1)
        assertThat(count.value).isEqualTo(6)
    }

    @Test
    fun `two screens share one upstream collection`() = runTest {
        val up = Upstream()
        val count = liveServedCount(up.servings(4, 2), backgroundScope)
        val hall = CopyOnWriteArrayList<Int>()
        val kitchen = CopyOnWriteArrayList<Int>()
        backgroundScope.launch { count.collect { hall += it } }
        backgroundScope.launch { count.collect { kitchen += it } }
        advanceTimeBy(250)
        assertThat(up.starts.get()).`as`("upstream collections").isEqualTo(1)
        assertThat(hall.last()).isEqualTo(6)
        assertThat(kitchen.last()).isEqualTo(6)
    }

    @Test
    fun `the upstream stops 5 seconds after the last screen leaves`() = runTest {
        val up = Upstream()
        val count = liveServedCount(up.servings(4), backgroundScope)
        val screen = backgroundScope.launch { count.collect { } }
        advanceTimeBy(1_000)
        screen.cancel()
        advanceTimeBy(4_900)
        assertThat(up.stops.get()).`as`("stopped 4.9 s after the last screen left").isZero()
        advanceTimeBy(200)
        assertThat(up.stops.get()).`as`("stopped 5.1 s after the last screen left").isEqualTo(1)
    }
}
