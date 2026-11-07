package workbench.events.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatIllegalStateException
import org.junit.jupiter.api.Test
import java.util.concurrent.CopyOnWriteArrayList

class DslTest {
    private val id = PaymentId("pay_7781")
    private val capture = PaymentCaptured(id, Money(1_999))
    private val refund = PaymentRefunded(id, Money(500))
    private val auth = PaymentAuthorized(id, Money(1_999))

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
        Callers.wireLedger(bus, timings, log)
        listOf(capture, refund, auth).forEach { bus.publish(it) }
        assertThat(log).containsExactly(
            "credit 19.99", "audit pay_7781",
            "debit 5.00", "audit pay_7781",
            "audit pay_7781",
        )
        assertThat(timings.calls("ledger")).`as`("only the handlers inside timed(\"ledger\") are timed").isEqualTo(2)
        assertThat(timings.totalNanos("ledger")).isEqualTo(2_000)
        assertThat(errors).isEmpty()
    }

    @Test
    fun `one handle closes everything the block subscribed, timed groups included`() {
        val log = CopyOnWriteArrayList<String>()
        val handle = Callers.wireLedger(bus, Timings(), log)
        assertThat(bus.handlerCount()).isEqualTo(3)
        handle.close()
        handle.close()
        assertThat(bus.handlerCount()).isZero()
        bus.publish(capture)
        assertThat(log).isEmpty()
    }

    @Test
    fun `a block that throws halfway subscribes nothing`() {
        assertThatIllegalStateException().isThrownBy { Callers.brokenWiring(bus) }.withMessageContaining("ledger account")
        assertThat(bus.handlerCount()).isZero()
    }

    @Test
    fun `subscribing from inside a handler fails loudly instead of being lost`() {
        Callers.subscribeFromInsideAHandler(bus)
        assertThat(bus.handlerCount()).isEqualTo(1)
        assertThat(bus.publish(capture)).isEqualTo(1)
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
        val seen = CopyOnWriteArrayList<PaymentEvent>()
        bus.subscriptions { on(MoneyMovement::class, Handler { seen += it }) }
        bus.subscribe(PaymentAuthorized::class.java, Handler { seen += it })
        listOf(capture, auth, refund).forEach { bus.publish(it) }
        assertThat(seen).containsExactly(capture, auth, refund)
    }
}
