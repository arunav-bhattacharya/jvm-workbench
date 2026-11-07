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
import java.util.concurrent.atomic.AtomicInteger
import kotlin.concurrent.thread
import workbench.coroutines.l08.PaymentStatus.AUTHORIZED
import workbench.coroutines.l08.PaymentStatus.CAPTURED
import workbench.coroutines.l08.PaymentStatus.PENDING
import workbench.coroutines.l08.PaymentStatus.REFUNDED

@OptIn(ExperimentalCoroutinesApi::class)
class HotFlowsTest {

    // ---- PaymentTracker.status ----

    @Test
    fun `status starts as PENDING and follows allowed moves only`() {
        val t = PaymentTracker("pay-1")
        assertThat(t.status.value).isEqualTo(PENDING)
        assertThat(t.moveTo(CAPTURED)).`as`("PENDING -> CAPTURED is not allowed").isFalse()
        assertThat(t.moveTo(AUTHORIZED)).isTrue()
        assertThat(t.moveTo(AUTHORIZED)).`as`("moving to the same status").isFalse()
        assertThat(t.moveTo(CAPTURED)).isTrue()
        assertThat(t.status.value).isEqualTo(CAPTURED)
    }

    /** Releases all [parties] threads at the same instant, again and again. Spins, so the threads line up tightly. */
    private class StartLine(private val parties: Int) {
        private val waiting = AtomicInteger()
        @Volatile private var round = 0
        fun await() {
            val r = round
            if (waiting.incrementAndGet() == parties) { waiting.set(0); round = r + 1; return }
            var spins = 0
            while (round == r) if (++spins % 1_000 == 0) Thread.yield() else Thread.onSpinWait()
        }
    }

    @Test
    fun `when 4 threads capture the same payment at once, exactly one wins`() {
        val trackers = List(10_000) { PaymentTracker("pay-$it").also { t -> t.moveTo(AUTHORIZED) } }
        val wins = List(trackers.size) { AtomicInteger() }
        val line = StartLine(4)
        val threads = List(4) {
            thread {
                for (i in trackers.indices) {
                    line.await() // all four threads try to capture payment i together
                    if (trackers[i].moveTo(CAPTURED)) wins[i].incrementAndGet()
                }
            }
        }
        threads.forEach { it.join() }
        assertThat(wins.count { it.get() > 1 }).`as`("payments captured more than once").isZero()
        assertThat(wins.count { it.get() == 1 }).`as`("payments captured exactly once").isEqualTo(trackers.size)
    }

    // ---- PaymentTracker.transitions ----

    @Test
    fun `a busy audit subscriber still receives every transition`() = runTest {
        val t = PaymentTracker("pay-1")
        val audited = CopyOnWriteArrayList<Transition>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
            t.transitions.collect { delay(100); audited += it } // writing to the audit table takes 100 ms
        }
        t.moveTo(AUTHORIZED)
        t.moveTo(CAPTURED)
        t.moveTo(REFUNDED)
        advanceTimeBy(1_000) // not advanceUntilIdle: it doesn't wait for work in backgroundScope
        assertThat(audited).containsExactly(
            Transition("pay-1", PENDING, AUTHORIZED), Transition("pay-1", AUTHORIZED, CAPTURED), Transition("pay-1", CAPTURED, REFUNDED),
        )
    }

    @Test
    fun `a late subscriber sees only transitions after it subscribed`() = runTest {
        val t = PaymentTracker("pay-1")
        t.moveTo(AUTHORIZED) // nobody is listening yet
        val audited = CopyOnWriteArrayList<Transition>()
        backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) { t.transitions.collect { audited += it } }
        t.moveTo(CAPTURED)
        runCurrent()
        assertThat(audited).containsExactly(Transition("pay-1", AUTHORIZED, CAPTURED))
    }

    // ---- liveCapturedTotal: stateIn with WhileSubscribed ----

    private class Upstream {
        val starts = AtomicInteger()
        val stops = AtomicInteger()
        fun captures(vararg cents: Long): Flow<Long> = flow {
            for (c in cents) { delay(100); emit(c) }
            delay(Long.MAX_VALUE) // a live feed never ends on its own
        }.onStart { starts.incrementAndGet() }.onCompletion { stops.incrementAndGet() }
    }

    @Test
    fun `the total does not collect until a dashboard subscribes`() = runTest {
        val up = Upstream()
        val total = liveCapturedTotal(up.captures(4_250, 990), backgroundScope)
        runCurrent()
        assertThat(up.starts.get()).`as`("upstream starts before anyone subscribed").isZero()
        assertThat(total.value).isZero()

        backgroundScope.launch { total.collect { } }
        advanceTimeBy(250)
        assertThat(up.starts.get()).isEqualTo(1)
        assertThat(total.value).isEqualTo(5_240)
    }

    @Test
    fun `two dashboards share one upstream collection`() = runTest {
        val up = Upstream()
        val total = liveCapturedTotal(up.captures(4_250, 990), backgroundScope)
        val a = CopyOnWriteArrayList<Long>()
        val b = CopyOnWriteArrayList<Long>()
        backgroundScope.launch { total.collect { a += it } }
        backgroundScope.launch { total.collect { b += it } }
        advanceTimeBy(250)
        assertThat(up.starts.get()).`as`("upstream collections").isEqualTo(1)
        assertThat(a.last()).isEqualTo(5_240)
        assertThat(b.last()).isEqualTo(5_240)
    }

    @Test
    fun `the upstream stops 5 seconds after the last dashboard leaves`() = runTest {
        val up = Upstream()
        val total = liveCapturedTotal(up.captures(4_250), backgroundScope)
        val dashboard = backgroundScope.launch { total.collect { } }
        advanceTimeBy(1_000)
        dashboard.cancel()
        advanceTimeBy(4_900)
        assertThat(up.stops.get()).`as`("stopped 4.9 s after the last dashboard left").isZero()
        advanceTimeBy(200)
        assertThat(up.stops.get()).`as`("stopped 5.1 s after the last dashboard left").isEqualTo(1)
    }
}
