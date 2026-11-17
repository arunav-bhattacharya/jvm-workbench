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
    private val id = ParcelId("PP-7781")
    private val booking = ParcelBooked(id, Weight(2_500))
    private val collection = ParcelCollected(id, Weight(2_500))
    private val delivery = ParcelDelivered(id, Weight(2_500))
    private val failure = DeliveryFailed(ParcelId("PP-7782"), FailReason.NOBODY_HOME)

    /** Records what each named handler saw, in one shared order. */
    private val seen: MutableList<String> = Collections.synchronizedList(mutableListOf())

    private fun <E : ParcelEvent> record(name: String) = Handler<E> { seen += "$name ${it::class.simpleName}" }

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
        bus.subscribe(ParcelCollected::class, record("collections"))
        bus.subscribe(ParcelDelivered::class, record("deliveries"))
        bus.publish(collection)
        assertThat(seen).containsExactly("collections ParcelCollected")
    }

    @Test
    fun `an event also reaches the handlers of every event supertype`() {
        val bus = quietBus()
        bus.subscribe(Handover::class, record("handovers"))
        bus.subscribe(ParcelEvent::class, record("tracking"))
        listOf(booking, collection, delivery, failure).forEach { bus.publish(it) }
        assertThat(seen.filter { it.startsWith("handovers") })
            .containsExactly("handovers ParcelCollected", "handovers ParcelDelivered")
        assertThat(seen.filter { it.startsWith("tracking") }).hasSize(4)
    }

    @Test
    fun `the most specific handlers run first, then each supertype, each in subscription order`() {
        val bus = quietBus()
        bus.subscribe(ParcelEvent::class, record("tracking"))
        bus.subscribe(Handover::class, record("handovers"))
        bus.subscribe(ParcelCollected::class, record("load"))
        bus.subscribe(ParcelCollected::class, record("texts"))
        bus.publish(collection)
        assertThat(seen).containsExactly(
            "load ParcelCollected", "texts ParcelCollected", "handovers ParcelCollected", "tracking ParcelCollected",
        )
    }

    @Test
    fun `publish returns the number of handlers it called`() {
        val bus = quietBus()
        assertThat(bus.publish(collection)).isZero()
        bus.subscribe(ParcelCollected::class, record("load"))
        bus.subscribe(ParcelEvent::class, record("tracking"))
        assertThat(bus.publish(collection)).isEqualTo(2)
        assertThat(bus.publish(booking)).isEqualTo(1)
        assertThat(bus.handlerCount()).isEqualTo(2)
    }

    @Test
    fun `the reified subscribe uses the type argument as the key`() {
        val bus = quietBus()
        Callers.onCollected(bus, record("load"))
        Callers.onHandover(bus, record("handovers"))
        bus.publish(delivery)
        bus.publish(collection)
        assertThat(seen).containsExactly("handovers ParcelDelivered", "load ParcelCollected", "handovers ParcelCollected")
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
        val errors = CopyOnWriteArrayList<Pair<ParcelEvent, Exception>>()
        val bus = EventBus(onError = { e, x -> errors += e to x })
        bus.subscribe(ParcelCollected::class) { throw IllegalStateException("load board is down") }
        bus.subscribe(ParcelCollected::class, record("texts"))
        bus.subscribe(ParcelEvent::class, record("tracking"))
        assertThat(bus.publish(collection)).isEqualTo(3)
        assertThat(seen).containsExactly("texts ParcelCollected", "tracking ParcelCollected")
        assertThat(errors).hasSize(1)
        assertThat(errors[0].first).isEqualTo(collection)
        assertThat(errors[0].second).hasMessage("load board is down")
    }

    @Test
    fun `closing a subscription stops delivery, and closing it twice is harmless`() {
        val bus = quietBus()
        val load = bus.subscribe(ParcelCollected::class, record("load"))
        val sameHandler = record<ParcelCollected>("twice")
        val first = bus.subscribe(ParcelCollected::class, sameHandler)
        bus.subscribe(ParcelCollected::class, sameHandler)
        load.close()
        load.close()
        first.close()
        bus.publish(collection)
        assertThat(seen).containsExactly("twice ParcelCollected")
        assertThat(bus.handlerCount()).isEqualTo(1)
    }

    @Test
    fun `a handler can unsubscribe itself while it is being called`() {
        val bus = quietBus()
        val handle = AtomicReference<Subscription>()
        handle.set(bus.subscribe(ParcelCollected::class) { seen += "once"; handle.get().close() })
        bus.subscribe(ParcelCollected::class, record("load"))
        bus.publish(collection)
        bus.publish(collection)
        assertThat(seen).containsExactly("once", "load ParcelCollected", "load ParcelCollected")
    }

    // ---- chain of responsibility ----

    @Test
    fun `middleware runs in list order on the way in, and in reverse on the way out`() {
        fun tracing(name: String) = Middleware { event, next ->
            seen += "$name in"
            try { next.proceed(event) } finally { seen += "$name out" }
        }
        val bus = quietBus(tracing("logging"), tracing("counting"))
        bus.subscribe(ParcelCollected::class, record("load"))
        assertThat(bus.publish(collection)).isEqualTo(1)
        assertThat(seen).containsExactly("logging in", "counting in", "load ParcelCollected", "counting out", "logging out")
    }

    @Test
    fun `a middleware can stop an event, and the bus keeps its own copy of the list`() {
        val list = mutableListOf<Middleware>(DropDuplicates())
        val bus = EventBus(list) { _, _ -> }
        list += Middleware { _, _ -> 0 }                 // added after construction: must not take effect
        bus.subscribe(ParcelCollected::class, record("load"))
        assertThat(bus.publish(collection)).isEqualTo(1)
        assertThat(bus.publish(ParcelCollected(id, Weight(2_500)))).isZero()   // equal: the same scan sent twice
        assertThat(bus.publish(ParcelCollected(id, Weight(2_600)))).isEqualTo(1)
        assertThat(seen).hasSize(2)
    }

    @Test
    fun `DropDuplicates passes each distinct event once when 8 threads publish the same events`() {
        val bus = quietBus(DropDuplicates())
        val delivered = AtomicInteger()
        bus.subscribe(ParcelEvent::class) { delivered.incrementAndGet() }
        val events = (1..2_000).map { ParcelCollected(ParcelId("PP-" + it.toString().padStart(4, '0')), Weight(it.toLong())) }
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
        bus.subscribe(ParcelCollected::class, record<ParcelCollected>("load").timed("load", timings))
        bus.publish(collection)
        bus.publish(collection)
        assertThat(seen).containsExactly("load ParcelCollected", "load ParcelCollected")
        assertThat(timings.calls("load")).isEqualTo(2)
        assertThat(timings.totalNanos("load")).isEqualTo(14_000_000)
    }

    @Test
    fun `timed records a call that throws, and lets the exception through`() {
        val timings = Timings(SteppingTicker(3))
        val failing = Handler<ParcelCollected> { throw IllegalStateException("boom") }.timed("load", timings)
        assertThatThrownBy { failing.handle(collection) }.isInstanceOf(IllegalStateException::class.java).hasMessage("boom")
        assertThat(timings.calls("load")).isEqualTo(1)
        assertThat(timings.totalNanos("load")).isEqualTo(3)
    }

    // ---- under load ----

    @Test
    fun `8 publishers and a thread that keeps subscribing and closing lose no events`() {
        val bus = quietBus()
        val collections = AtomicInteger()
        val all = AtomicInteger()
        bus.subscribe(ParcelCollected::class) { collections.incrementAndGet() }
        bus.subscribe(ParcelEvent::class) { all.incrementAndGet() }
        val stop = AtomicBoolean()
        val failure = AtomicReference<Throwable>()
        val churn = thread {
            try {
                while (!stop.get()) bus.subscribe(Handover::class) { }.close()
            } catch (t: Throwable) {
                failure.set(t)
            }
        }
        collide(8) { repeat(10_000) { bus.publish(collection); bus.publish(booking) } }
        stop.set(true)
        churn.join()
        assertThat(failure.get()).isNull()
        assertThat(collections.get()).isEqualTo(80_000)
        assertThat(all.get()).isEqualTo(160_000)
    }
}
