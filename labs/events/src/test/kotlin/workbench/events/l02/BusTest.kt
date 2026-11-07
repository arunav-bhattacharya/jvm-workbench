package workbench.events.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.util.Collections
import java.util.concurrent.CopyOnWriteArrayList
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicBoolean
import java.util.concurrent.atomic.AtomicInteger
import java.util.concurrent.atomic.AtomicReference
import kotlin.concurrent.thread
import kotlin.reflect.KClass
import kotlin.reflect.KVariance

class BusTest {
    private val id = PaymentId("pay_7781")
    private val auth = PaymentAuthorized(id, Money(1_999))
    private val capture = PaymentCaptured(id, Money(1_999))
    private val refund = PaymentRefunded(id, Money(500))
    private val decline = PaymentDeclined(PaymentId("pay_7782"), DeclineReason.CARD_EXPIRED)

    /** Records what each named handler saw, in one shared order. */
    private val seen: MutableList<String> = Collections.synchronizedList(mutableListOf())

    private fun <E : PaymentEvent> record(name: String) = Handler<E> { seen += "$name ${it::class.simpleName}" }

    private fun quietBus(vararg middleware: Middleware) = EventBus(middleware.toList()) { _, _ -> }

    // the tests use their own start line, so a bug elsewhere doesn't hide these results
    private fun collide(threads: Int, task: (Int) -> Unit) {
        val go = CountDownLatch(1)
        val ts = (0 until threads).map { i -> thread { go.await(); task(i) } }
        go.countDown()
        ts.forEach { it.join() }
    }

    // ---- dispatch ----

    @Test
    fun `an event reaches the handlers of its own class, and not of its siblings`() {
        val bus = quietBus()
        bus.subscribe(PaymentCaptured::class, record("captures"))
        bus.subscribe(PaymentRefunded::class, record("refunds"))
        bus.publish(capture)
        assertThat(seen).containsExactly("captures PaymentCaptured")
    }

    @Test
    fun `an event also reaches the handlers of every event supertype`() {
        val bus = quietBus()
        bus.subscribe(MoneyMovement::class, record("movements"))
        bus.subscribe(PaymentEvent::class, record("audit"))
        listOf(auth, capture, refund, decline).forEach { bus.publish(it) }
        assertThat(seen.filter { it.startsWith("movements") })
            .containsExactly("movements PaymentCaptured", "movements PaymentRefunded")
        assertThat(seen.filter { it.startsWith("audit") }).hasSize(4)
    }

    @Test
    fun `the most specific handlers run first, then each supertype, each in subscription order`() {
        val bus = quietBus()
        bus.subscribe(PaymentEvent::class, record("audit"))
        bus.subscribe(MoneyMovement::class, record("movements"))
        bus.subscribe(PaymentCaptured::class, record("ledger"))
        bus.subscribe(PaymentCaptured::class, record("receipts"))
        bus.publish(capture)
        assertThat(seen).containsExactly(
            "ledger PaymentCaptured", "receipts PaymentCaptured", "movements PaymentCaptured", "audit PaymentCaptured",
        )
    }

    @Test
    fun `publish returns the number of handlers it called`() {
        val bus = quietBus()
        assertThat(bus.publish(capture)).isZero()
        bus.subscribe(PaymentCaptured::class, record("ledger"))
        bus.subscribe(PaymentEvent::class, record("audit"))
        assertThat(bus.publish(capture)).isEqualTo(2)
        assertThat(bus.publish(auth)).isEqualTo(1)
        assertThat(bus.handlerCount()).isEqualTo(2)
    }

    @Test
    fun `the reified subscribe uses the type argument as the key`() {
        val bus = quietBus()
        Callers.onCaptured(bus, record("ledger"))
        Callers.onMoneyMovement(bus, record("movements"))
        bus.publish(refund)
        bus.publish(capture)
        assertThat(seen).containsExactly("movements PaymentRefunded", "ledger PaymentCaptured", "movements PaymentCaptured")
    }

    // ---- variance ----

    @Test
    fun `Handler is declared in, because a handler only consumes events`() {
        assertThat(Handler::class.typeParameters.single().variance).isEqualTo(KVariance.IN)
    }

    @Test
    fun `Java callers see subscribe taking a Handler of ? super E`() {
        val method = EventBus::class.java.getMethod("subscribe", KClass::class.java, Handler::class.java)
        assertThat(method.genericParameterTypes[1].typeName).isEqualTo("workbench.events.l02.Handler<? super E>")
    }

    // ---- observer bookkeeping ----

    @Test
    fun `a failing handler does not stop the others, and the error handler hears about it`() {
        val errors = CopyOnWriteArrayList<Pair<PaymentEvent, Exception>>()
        val bus = EventBus(onError = { e, x -> errors += e to x })
        bus.subscribe(PaymentCaptured::class) { throw IllegalStateException("ledger is down") }
        bus.subscribe(PaymentCaptured::class, record("receipts"))
        bus.subscribe(PaymentEvent::class, record("audit"))
        assertThat(bus.publish(capture)).isEqualTo(3)
        assertThat(seen).containsExactly("receipts PaymentCaptured", "audit PaymentCaptured")
        assertThat(errors).hasSize(1)
        assertThat(errors[0].first).isEqualTo(capture)
        assertThat(errors[0].second).hasMessage("ledger is down")
    }

    @Test
    fun `closing a subscription stops delivery, and closing it twice is harmless`() {
        val bus = quietBus()
        val ledger = bus.subscribe(PaymentCaptured::class, record("ledger"))
        val sameHandler = record<PaymentCaptured>("twice")
        val first = bus.subscribe(PaymentCaptured::class, sameHandler)
        bus.subscribe(PaymentCaptured::class, sameHandler)
        ledger.close()
        ledger.close()
        first.close()
        bus.publish(capture)
        assertThat(seen).containsExactly("twice PaymentCaptured")
        assertThat(bus.handlerCount()).isEqualTo(1)
    }

    @Test
    fun `a handler can unsubscribe itself while it is being called`() {
        val bus = quietBus()
        val handle = AtomicReference<Subscription>()
        handle.set(bus.subscribe(PaymentCaptured::class) { seen += "once"; handle.get().close() })
        bus.subscribe(PaymentCaptured::class, record("ledger"))
        bus.publish(capture)
        bus.publish(capture)
        assertThat(seen).containsExactly("once", "ledger PaymentCaptured", "ledger PaymentCaptured")
    }

    // ---- chain of responsibility ----

    @Test
    fun `middleware runs in list order on the way in, and in reverse on the way out`() {
        fun tracing(name: String) = Middleware { event, next ->
            seen += "$name in"
            try { next.proceed(event) } finally { seen += "$name out" }
        }
        val bus = quietBus(tracing("logging"), tracing("tracing"))
        bus.subscribe(PaymentCaptured::class, record("ledger"))
        assertThat(bus.publish(capture)).isEqualTo(1)
        assertThat(seen).containsExactly("logging in", "tracing in", "ledger PaymentCaptured", "tracing out", "logging out")
    }

    @Test
    fun `a middleware can stop an event, and the bus keeps its own copy of the list`() {
        val list = mutableListOf<Middleware>(DropDuplicates())
        val bus = EventBus(list) { _, _ -> }
        list += Middleware { _, _ -> 0 }                 // added after construction: must not take effect
        bus.subscribe(PaymentCaptured::class, record("ledger"))
        assertThat(bus.publish(capture)).isEqualTo(1)
        assertThat(bus.publish(PaymentCaptured(id, Money(1_999)))).isZero()   // equal: a redelivery
        assertThat(bus.publish(PaymentCaptured(id, Money(2_000)))).isEqualTo(1)
        assertThat(seen).hasSize(2)
    }

    @Test
    fun `DropDuplicates passes each distinct event once when 8 threads publish the same events`() {
        val bus = quietBus(DropDuplicates())
        val delivered = AtomicInteger()
        bus.subscribe(PaymentEvent::class) { delivered.incrementAndGet() }
        val events = (1..2_000).map { PaymentCaptured(PaymentId("pay_" + it.toString().padStart(4, '0')), Money(it.toLong())) }
        collide(8) { events.forEach(bus::publish) }
        assertThat(delivered.get()).isEqualTo(events.size)
    }

    // ---- decorator ----

    /** Virtual time: every read moves the clock forward by [step] nanoseconds. */
    private class SteppingTicker(private val step: Long) : Ticker {
        private var now = 0L
        override fun nanos(): Long { now += step; return now }
    }

    @Test
    fun `timed records the elapsed time of each call under its name`() {
        val timings = Timings(SteppingTicker(7_000_000))
        val bus = quietBus()
        bus.subscribe(PaymentCaptured::class, record<PaymentCaptured>("ledger").timed("ledger", timings))
        bus.publish(capture)
        bus.publish(capture)
        assertThat(seen).containsExactly("ledger PaymentCaptured", "ledger PaymentCaptured")
        assertThat(timings.calls("ledger")).isEqualTo(2)
        assertThat(timings.totalNanos("ledger")).isEqualTo(14_000_000)
    }

    @Test
    fun `timed records a call that throws, and lets the exception through`() {
        val timings = Timings(SteppingTicker(3))
        val failing = Handler<PaymentCaptured> { throw IllegalStateException("boom") }.timed("ledger", timings)
        assertThatThrownBy { failing.handle(capture) }.isInstanceOf(IllegalStateException::class.java).hasMessage("boom")
        assertThat(timings.calls("ledger")).isEqualTo(1)
        assertThat(timings.totalNanos("ledger")).isEqualTo(3)
    }

    // ---- under load ----

    @Test
    fun `8 publishers and a thread that keeps subscribing and closing lose no events`() {
        val bus = quietBus()
        val captures = AtomicInteger()
        val all = AtomicInteger()
        bus.subscribe(PaymentCaptured::class) { captures.incrementAndGet() }
        bus.subscribe(PaymentEvent::class) { all.incrementAndGet() }
        val stop = AtomicBoolean()
        val failure = AtomicReference<Throwable>()
        val churn = thread {
            try {
                while (!stop.get()) bus.subscribe(MoneyMovement::class) { }.close()
            } catch (t: Throwable) {
                failure.set(t)
            }
        }
        collide(8) { repeat(10_000) { bus.publish(capture); bus.publish(auth) } }
        stop.set(true)
        churn.join()
        assertThat(failure.get()).isNull()
        assertThat(captures.get()).isEqualTo(80_000)
        assertThat(all.get()).isEqualTo(160_000)
    }
}
