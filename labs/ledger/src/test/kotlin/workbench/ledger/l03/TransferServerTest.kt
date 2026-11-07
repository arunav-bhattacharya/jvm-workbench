package workbench.ledger.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import org.junit.jupiter.api.assertTimeoutPreemptively
import java.lang.management.ManagementFactory
import java.time.Duration
import java.util.concurrent.Callable
import java.util.concurrent.CountDownLatch
import java.util.concurrent.Executors
import java.util.concurrent.ThreadLocalRandom
import java.util.concurrent.TimeUnit
import java.util.concurrent.TimeoutException
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger

class TransferServerTest {

    private fun accounts(n: Int, each: Long): Map<String, Long> = (0 until n).associate { "acc-%02d".format(it) to each }

    private fun randomTransfer(ids: List<String>, id: String, maxCents: Long): Transfer {
        val rnd = ThreadLocalRandom.current()
        val a = rnd.nextInt(ids.size)
        var b = rnd.nextInt(ids.size - 1)
        if (b >= a) b++
        return Transfer(id, ids[a], ids[b], 1 + rnd.nextLong(maxCents))
    }

    private val small = Transfer("t-small", "alice", "bob", 1_000)

    /** A remote check that never answers until it is interrupted, and records that it was. */
    private class Stuck : Check {
        val entered = CountDownLatch(1)
        val interrupted = CountDownLatch(1)
        override fun passes(t: Transfer): Boolean {
            entered.countDown()
            try {
                CountDownLatch(1).await()
            } catch (e: InterruptedException) {
                interrupted.countDown()
                throw e
            }
            return true
        }
    }

    @Test
    fun `the bulkhead never lets more calls in than it has permits`() {
        val bulkhead = Bulkhead(20)
        val inside = AtomicInteger()
        val most = AtomicInteger()
        Executors.newVirtualThreadPerTaskExecutor().use { vt ->
            val calls = List(2_000) {
                vt.submit(Callable {
                    bulkhead.call(Duration.ofSeconds(30).toNanos()) {
                        most.accumulateAndGet(inside.incrementAndGet(), ::maxOf)
                        Thread.sleep(2)
                        inside.decrementAndGet()
                    }
                })
            }
            calls.forEach { it.get() }
        }
        assertThat(most.get()).`as`("most calls inside at once").isLessThanOrEqualTo(20).isGreaterThanOrEqualTo(2)
        assertThat(bulkhead.available()).`as`("every permit came back").isEqualTo(20)
    }

    @Test
    fun `the bulkhead gives up after its wait and never runs the call`() {
        val bulkhead = Bulkhead(1)
        val holding = CountDownLatch(1)
        val release = CountDownLatch(1)
        val holder = Thread.ofVirtual().start {
            bulkhead.call(Duration.ofSeconds(10).toNanos()) { holding.countDown(); release.await() }
        }
        try {
            assertThat(holding.await(5, TimeUnit.SECONDS)).`as`("the holder got the only permit").isTrue()
            val ran = AtomicBoolean()
            assertThatThrownBy { bulkhead.call(Duration.ofMillis(50).toNanos()) { ran.set(true) } }
                .isInstanceOf(TimeoutException::class.java)
            assertThat(ran.get()).`as`("the call ran without a permit").isFalse()
            assertThat(bulkhead.available()).isZero()
        } finally {
            release.countDown()
            holder.join(5_000)
        }
        assertThat(bulkhead.available()).isEqualTo(1)
    }

    @Test
    fun `the bulkhead gives its permit back when the call throws or is interrupted`() {
        val bulkhead = Bulkhead(2)
        assertThatThrownBy { bulkhead.call(1_000_000_000) { throw IllegalStateException("fraud service: 503") } }
            .isInstanceOf(IllegalStateException::class.java)
        assertThat(bulkhead.available()).isEqualTo(2)

        val stuck = Stuck()
        val caller = Thread.ofVirtual().start {
            try { bulkhead.call(1_000_000_000) { stuck.passes(small) } } catch (e: InterruptedException) { }
        }
        assertThat(stuck.entered.await(5, TimeUnit.SECONDS)).isTrue()
        caller.interrupt()
        caller.join(5_000)
        assertThat(bulkhead.available()).isEqualTo(2)
    }

    @Test
    fun `both checks pass in time and the transfer is approved`() {
        val screening = Screening({ true }, { true }, Bulkhead(5), Duration.ofSeconds(5), 5_000)
        assertThat(screening.screen(small)).isEqualTo(Verdict.APPROVED)
    }

    @Test
    fun `a check that says no declines at once and interrupts the other one`() {
        val fraud = Stuck()
        val screening = Screening(fraud, { false }, Bulkhead(5), Duration.ofSeconds(60), 5_000)
        val verdict = assertTimeoutPreemptively(Duration.ofSeconds(10)) { screening.screen(small) }
        assertThat(verdict).isEqualTo(Verdict.DECLINED)
        assertThat(fraud.interrupted.await(5, TimeUnit.SECONDS)).`as`("the stuck fraud call was interrupted").isTrue()
    }

    @Test
    fun `a check that throws declines at once and interrupts the other one`() {
        val fraud = Stuck()
        val screening = Screening(fraud, { throw IllegalStateException("limits service: 503") }, Bulkhead(5),
            Duration.ofSeconds(60), 5_000)
        val verdict = assertTimeoutPreemptively(Duration.ofSeconds(10)) { screening.screen(small) }
        assertThat(verdict).isEqualTo(Verdict.DECLINED)
        assertThat(fraud.interrupted.await(5, TimeUnit.SECONDS)).`as`("the stuck fraud call was interrupted").isTrue()
    }

    @Test
    fun `at the deadline small transfers go through in stand-in and large ones time out`() {
        for ((cents, expected) in listOf(1_000L to Verdict.STAND_IN, 50_000L to Verdict.TIMED_OUT)) {
            val fraud = Stuck()
            val bulkhead = Bulkhead(3)
            val screening = Screening(fraud, { true }, bulkhead, Duration.ofMillis(100), 5_000)
            val verdict = assertTimeoutPreemptively(Duration.ofSeconds(10)) {
                screening.screen(Transfer("t-$cents", "alice", "bob", cents))
            }
            assertThat(verdict).`as`("verdict for $cents cents").isEqualTo(expected)
            assertThat(fraud.interrupted.await(5, TimeUnit.SECONDS)).`as`("the stuck fraud call was interrupted").isTrue()
            assertThat(bulkhead.available()).`as`("its permit came back").isEqualTo(3)
        }
    }

    @Test
    fun `a full bulkhead falls back without calling the fraud service`() {
        val bulkhead = Bulkhead(1)
        val holding = CountDownLatch(1)
        val release = CountDownLatch(1)
        val holder = Thread.ofVirtual().start {
            bulkhead.call(Duration.ofSeconds(10).toNanos()) { holding.countDown(); release.await() }
        }
        try {
            assertThat(holding.await(5, TimeUnit.SECONDS)).isTrue()
            val called = AtomicBoolean()
            val screening = Screening({ called.set(true); true }, { true }, bulkhead, Duration.ofMillis(100), 5_000)
            val verdict = assertTimeoutPreemptively(Duration.ofSeconds(10)) { screening.screen(small) }
            assertThat(verdict).isEqualTo(Verdict.STAND_IN)
            assertThat(called.get()).`as`("the fraud service was called without a permit").isFalse()
        } finally {
            release.countDown()
            holder.join(5_000)
        }
    }

    @Test
    fun `every request runs on its own virtual thread, all at the same time`() {
        val n = 500
        val ledger = Ledger(accounts(10, 1_000_000))
        val service = LedgerService.start(ledger, Journal.NONE, PoolPlan(4, 10_000))
        val mx = ManagementFactory.getThreadMXBean()
        val platformBefore = mx.threadCount
        val platformMost = AtomicInteger()
        val arrived = CountDownLatch(n)
        // each limits check waits until all n requests are in flight: only a thread per request gets there
        val limits = Check {
            arrived.countDown()
            val all = arrived.await(15, TimeUnit.SECONDS)
            platformMost.accumulateAndGet(mx.threadCount, ::maxOf)
            all
        }
        val server = TransferServer(service, Screening({ true }, limits, Bulkhead(n), Duration.ofSeconds(30), 0))
        val requests = List(n) { randomTransfer(ledger.accountIds(), "r$it", 100) }
        try {
            val replies = server.serveAll(requests)
            assertThat(replies.map { it.transferId }).isEqualTo(requests.map { it.id() })
            assertThat(replies).allMatch { it.status == Status.APPLIED }
        } finally {
            service.shutdown(Duration.ofSeconds(5))
        }
        assertThat(platformMost.get() - platformBefore)
            .`as`("platform threads added while $n requests were in flight").isLessThan(200)
    }

    @Test
    fun `10,000 concurrent requests keep the books exact and the fraud bulkhead at its limit`() {
        val opening = accounts(50, 100_000)                     // 5,000,000 cents
        val ledger = Ledger(opening)
        val service = LedgerService.start(ledger, Journal.NONE, PoolPlan(4, 20_000))
        val inside = AtomicInteger()
        val most = AtomicInteger()
        val fraud = Check { t ->
            most.accumulateAndGet(inside.incrementAndGet(), ::maxOf)
            try {
                Thread.sleep(ThreadLocalRandom.current().nextLong(3))
                !t.id().endsWith("7")                           // about one in ten looks like fraud
            } finally {
                inside.decrementAndGet()
            }
        }
        val bulkhead = Bulkhead(50)
        val server = TransferServer(service, Screening(fraud, { true }, bulkhead, Duration.ofSeconds(10), 2_000))
        val requests = List(10_000) { randomTransfer(ledger.accountIds(), "r$it", 20_000) }

        val replies = server.serveAll(requests)
        val report = service.shutdown(Duration.ofSeconds(10))

        assertThat(replies).hasSize(10_000)
        assertThat(replies.map { it.transferId }).isEqualTo(requests.map { it.id() })
        assertThat(report.drained()).isTrue()
        // replay every APPLIED reply on the opening balances: the ledger must match exactly
        val expected = HashMap(opening)
        replies.zip(requests).filter { (reply, _) -> reply.status == Status.APPLIED }.forEach { (_, t) ->
            expected.merge(t.from(), -t.cents()) { a, b -> a + b }
            expected.merge(t.to(), t.cents()) { a, b -> a + b }
        }
        val end = ledger.snapshot()
        assertThat(end.balances()).`as`("balances replayed from the replies").isEqualTo(expected)
        assertThat(end.total()).isEqualTo(5_000_000)
        assertThat(end.balances().values).allMatch { it >= 0 }
        assertThat(replies.count { it.status == Status.DECLINED }).`as`("fraud declines").isPositive()
        assertThat(most.get()).`as`("most fraud calls in flight").isLessThanOrEqualTo(50).isGreaterThanOrEqualTo(2)
        assertThat(bulkhead.available()).isEqualTo(50)
    }
}
