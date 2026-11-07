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

    @Test
    fun `when two threads capture the same payment, exactly one wins`() {
        // the hook holds each thread until both have passed the status check, so the two
        // moves always overlap (a real limit check would take a few ms and overlap by chance)
        val bothChecked = CyclicBarrier(2)
        val t = PaymentTracker("pay-1") { tr -> if (tr.to == CAPTURED) runCatching { bothChecked.await(2, TimeUnit.SECONDS) } }
        t.moveTo(AUTHORIZED)
        val results = CopyOnWriteArrayList<Boolean>()
        val threads = List(2) { thread { results += t.moveTo(CAPTURED) } }
        threads.forEach { it.join() }
        assertThat(results).`as`("what the two moveTo(CAPTURED) calls returned").containsExactlyInAnyOrder(true, false)
        assertThat(t.status.value).isEqualTo(CAPTURED)
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
