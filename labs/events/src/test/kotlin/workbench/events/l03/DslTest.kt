package workbench.events.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatIllegalStateException
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList

class DslTest {
    private val id = ParcelId("PP-7781")
    private val collection = ParcelCollected(id, Weight(2_500))
    private val delivery = ParcelDelivered(id, Weight(1_200))
    private val booking = ParcelBooked(id, Weight(2_500))

    private val errors = CopyOnWriteArrayList<Exception>()
    private val bus = EventBus(emptyList()) { _, e -> errors += e }

    /** Virtual time: every read moves the clock forward by [step] nanoseconds. */
    private class SteppingTicker(private val step: Long) : Ticker {
        private var now = 0L
        override fun nanos(): Long { now += step; return now }
    }

    @Test
    fun `a subscriptions block wires handlers and timed groups in one go`() {
        val log = CopyOnWriteArrayList<String>()
        val timings = Timings(SteppingTicker(1_000))
        Callers.wireLoadBoard(bus, timings, log)
        listOf(collection, delivery, booking).forEach { bus.publish(it) }
        assertThat(log).containsExactly(
            "load 2.5 kg", "tracking PP-7781",
            "unload 1.2 kg", "tracking PP-7781",
            "tracking PP-7781",
        )
        assertThat(timings.calls("load")).`as`("only the handlers inside timed(\"load\") are timed").isEqualTo(2)
        assertThat(timings.totalNanos("load")).isEqualTo(2_000)
        assertThat(errors).isEmpty()
    }

    @Test
    fun `one handle closes everything the block subscribed, timed groups included`() {
        val log = CopyOnWriteArrayList<String>()
        val handle = Callers.wireLoadBoard(bus, Timings(), log)
        assertThat(bus.handlerCount()).isEqualTo(3)
        handle.close()
        handle.close()
        assertThat(bus.handlerCount()).isZero()
        bus.publish(collection)
        assertThat(log).isEmpty()
    }

    @Test
    fun `a block that throws halfway subscribes nothing`() {
        assertThatIllegalStateException().isThrownBy { Callers.brokenWiring(bus) }.withMessageContaining("load limit")
        assertThat(bus.handlerCount()).isZero()
    }

    @Test
    fun `subscribing from inside a handler fails loudly instead of being lost`() {
        Callers.subscribeFromInsideAHandler(bus)
        assertThat(bus.handlerCount()).isEqualTo(1)
        assertThat(bus.publish(collection)).isEqualTo(1)
        assertThat(errors).singleElement().isInstanceOf(IllegalStateException::class.java)
        assertThat(errors[0]).hasMessageContaining("committed")
        assertThat(bus.handlerCount()).isEqualTo(1)
    }

    @Test
    fun `the builders are marked with a DSL marker annotation`() {
        assertThat(SubscriptionsBuilder::class.java.isAnnotationPresent(EventsDsl::class.java)).isTrue()
        assertThat(TimedGroup::class.java.isAnnotationPresent(EventsDsl::class.java)).isTrue()
    }

    @Test
    fun `the non-reified on and the Class overload of subscribe work from Kotlin too`() {
        val seen = CopyOnWriteArrayList<ParcelEvent>()
        bus.subscriptions { on(Handover::class, Handler { seen += it }) }
        bus.subscribe(ParcelBooked::class.java, Handler { seen += it })
        listOf(collection, booking, delivery).forEach { bus.publish(it) }
        assertThat(seen).containsExactly(collection, booking, delivery)
    }
}
