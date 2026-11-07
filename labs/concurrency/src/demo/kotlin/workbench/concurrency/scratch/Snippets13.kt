package workbench.concurrency.scratch

import java.util.concurrent.CountDownLatch
import java.util.concurrent.TimeUnit
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicLong
import java.util.function.Consumer
import java.util.function.Predicate
import java.util.function.Supplier
import kotlin.concurrent.thread

// stand-ins with the lab's signatures
object Stress {
    @JvmStatic
    fun <S> failingRounds(rounds: Int, threads: Int, perThread: Int, setup: Supplier<S>, actor: Consumer<S>, invariant: Predicate<S>): Int = 0
}
class RefundLedger(captured: Map<String, Long>) {
    fun refund(paymentId: String, cents: Long): Boolean = true
    fun refunded(paymentId: String): Long = 0
}
fun <T> assertThat(x: T) = x

class Round(val ledger: RefundLedger, val approved: AtomicLong)

fun s13Stress() {
    val failed = Stress.failingRounds(20, 8, 2_000,
        { Round(RefundLedger(mapOf("pay-1" to 10_000L)), AtomicLong()) },              // fresh state per round
        { r -> if (r.ledger.refund("pay-1", 1)) r.approved.incrementAndGet() },        // every thread, over and over
        { r -> r.approved.get() == 10_000L && r.ledger.refunded("pay-1") == 10_000L }) // must hold at the end
    check(failed == 0)
}

enum class S13Status { PENDING, SETTLED }
class S13Payment(val id: String)
class S13Store {
    fun status(id: String) = S13Status.SETTLED
    fun onSettled(listener: (String) -> Unit) {}
}
class S13Worker { fun submit(p: S13Payment) {} }

fun s13Flaky(worker: S13Worker, store: S13Store, payment: S13Payment) {
    // flaky: hopes 50 ms is enough on every machine, and is slow on all of them
    worker.submit(payment)
    Thread.sleep(50)
    check(store.status(payment.id) == S13Status.SETTLED)

    // solid: wait for the event itself, with a deadline far above any real duration
    val settled = CountDownLatch(1)
    store.onSettled { settled.countDown() }
    worker.submit(payment)
    check(settled.await(10, TimeUnit.SECONDS))
    check(store.status(payment.id) == S13Status.SETTLED)
}

class S13Request
enum class S13Result { APPROVED }
interface Issuer { fun authorize(r: S13Request): S13Result }

class BlockingIssuer : Issuer {
    val inCall = CountDownLatch(1)
    val release = CountDownLatch(1)

    override fun authorize(r: S13Request): S13Result {
        inCall.countDown()           // 1. tell the test: a thread is inside the call
        release.await()              // 2. hold it here until the test says go
        return S13Result.APPROVED
    }
}

class S13BinCache(private val loader: (String) -> String) { fun issuerFor(bin: String) = loader(bin) }

fun s13Flaky2() {
    val loads = AtomicInteger()
    val cache = S13BinCache { loads.incrementAndGet(); "Northwind Bank" }
    repeat(8) { thread { cache.issuerFor("411111") } }
    Thread.sleep(100)                                   // "they should be done by now"
    check(loads.get() == 1)
}

fun awaitParked(threads: List<Thread>, n: Int) {
    val deadline = System.nanoTime() + TimeUnit.SECONDS.toNanos(5)
    while (threads.count { it.state == Thread.State.BLOCKED || it.state == Thread.State.WAITING } < n) {
        check(System.nanoTime() < deadline) { "callers never queued up" }
        Thread.sleep(5)
    }
}

fun s13Solid() {
    val loads = AtomicInteger()
    val inLoader = CountDownLatch(1)
    val release = CountDownLatch(1)
    val cache = S13BinCache {
        loads.incrementAndGet()
        inLoader.countDown()                               // 1. a caller is inside the loader
        release.await()                                    //    and stays there until we say go
        "Northwind Bank"
    }
    val callers = List(8) { thread { cache.issuerFor("411111") } }
    check(inLoader.await(5, TimeUnit.SECONDS))
    awaitParked(callers, 8)                                // 2. all 8 are now waiting, inside or outside
    release.countDown()                                    // 3. let the load finish
    callers.forEach { it.join() }
    check(loads.get() == 1)                                // 4. one load served all eight
}

class S13Counter { private val n = AtomicInteger(); fun increment() { n.incrementAndGet() }; fun total() = n.get() }

fun `counts every increment from 8 threads`() {
    val counter = S13Counter()
    val go = CountDownLatch(1)
    val threads = List(8) { thread { go.await(); repeat(50_000) { counter.increment() } } }
    go.countDown()
    threads.forEach { it.join() }
    check(counter.total() == 8 * 50_000)
}
