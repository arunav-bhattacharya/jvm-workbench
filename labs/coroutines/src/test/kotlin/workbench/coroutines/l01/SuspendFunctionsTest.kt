package workbench.coroutines.l01

import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceUntilIdle
import kotlinx.coroutines.test.currentTime
import kotlinx.coroutines.test.runCurrent
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.concurrent.thread
import kotlin.time.Duration.Companion.seconds

/** A fake bakery. If [reply] is set, it answers on a separate thread, like the real one. */
private class FakeBakery(private val reply: ((OrderCallback) -> Unit)? = null) : BakeryClient {
    val orders = CopyOnWriteArrayList<BreadOrder>()
    val cancels = AtomicInteger()
    val callback = AtomicReference<OrderCallback>()

    override fun order(order: BreadOrder, callback: OrderCallback): PendingOrder {
        orders += order
        this.callback.set(callback)
        reply?.let { r -> thread(name = "bakery-library") { r(callback) } }
        return PendingOrder { cancels.incrementAndGet() }
    }
}

@OptIn(ExperimentalCoroutinesApi::class)
class SuspendFunctionsTest {
    private val order = BreadOrder("sourdough", 2)
    private val ready = Pickup("T-17", 2)

    @Test
    fun `orderAwait returns the pickup the bakery sends`() = runTest(timeout = 10.seconds) {
        val bakery = FakeBakery { it.onReady(ready) }
        assertThat(bakery.orderAwait(order)).isEqualTo(ready)
        assertThat(bakery.orders).containsExactly(order)
    }

    @Test
    fun `orderAwait throws the error the bakery reports`() = runTest(timeout = 10.seconds) {
        val bakery = FakeBakery { it.onFailed(SoldOutException("no sourdough left today")) }
        val thrown = try {
            bakery.orderAwait(order)
            null
        } catch (e: SoldOutException) {
            e
        }
        assertThat(thrown).isNotNull()
        assertThat(thrown!!.reason).isEqualTo("no sourdough left today")
    }

    @Test
    fun `cancelling the caller cancels the order`() = runTest(timeout = 10.seconds) {
        val bakery = FakeBakery(reply = null) // never answers on its own
        val job = launch { bakery.orderAwait(order) }
        runCurrent() // the coroutine starts, places the order and suspends
        assertThat(bakery.orders).hasSize(1)

        job.cancelAndJoin() // hangs here if the wait is not cancellable

        assertThat(job.isCancelled).isTrue()
        assertThat(bakery.cancels.get()).`as`("PendingOrder.cancel() calls").isEqualTo(1)
    }

    @Test
    fun `a late reply after cancellation is ignored`() = runTest(timeout = 10.seconds) {
        val bakery = FakeBakery(reply = null)
        val job = launch { bakery.orderAwait(order) }
        runCurrent()
        job.cancelAndJoin()

        val lateError = AtomicReference<Throwable>()
        thread { runCatching { bakery.callback.get().onReady(ready) }.onFailure(lateError::set) }.join()

        assertThat(lateError.get()).`as`("exception from the late callback").isNull()
        assertThat(job.isCancelled).isTrue()
    }

    @Test
    fun `pauseBeforeRetry lets other coroutines run while it waits`() = runTest {
        val log = CopyOnWriteArrayList<String>()
        repeat(3) { i ->
            launch {
                log += "start $i"
                pauseBeforeRetry(200)
                log += "end $i"
            }
        }
        advanceUntilIdle()
        // all three wait at the same time, on one thread, so they all start before any ends
        assertThat(log).containsExactly("start 0", "start 1", "start 2", "end 0", "end 1", "end 2")
        assertThat(currentTime).`as`("virtual time").isEqualTo(200)
    }
}
