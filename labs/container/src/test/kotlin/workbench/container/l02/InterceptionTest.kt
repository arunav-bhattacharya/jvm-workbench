package workbench.container.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.lang.reflect.Proxy
import java.util.concurrent.atomic.AtomicLong
import java.util.function.LongSupplier

class InterceptionTest {
    private val ticks = AtomicLong()
    private val clock = LongSupplier { ticks.addAndGet(1_000_000) }   // 1 ms per read
    private val log = CallLog()

    private fun app() = Container(
        listOf(BookingScript::class.java, FakeBooking::class.java, ShowArchive::class.java,
            ShowCloser::class.java, ReviewFetcher::class.java, PlainFinal::class.java),
        Interception(log, clock),
    )

    @Test
    fun `retries reserve until the booking service answers, and times the call once`() {
        val c = app()
        val script = c.get(BookingScript::class.java)
        script.reserveFailures.set(2)
        assertThat(c.get(BookingClient::class.java).reserve("C12", 12_000)).isEqualTo("hold-C12")
        assertThat(script.reserveCalls.get()).`as`("calls the booking service saw").isEqualTo(3)
        assertThat(log.calls()).containsExactly(Call("BookingClient.reserve", 1_000_000, false))
    }

    @Test
    fun `gives up after the last attempt and rethrows the booking service's own exception`() {
        val c = app()
        val script = c.get(BookingScript::class.java)
        script.reserveFailures.set(5)
        assertThatThrownBy { c.get(BookingClient::class.java).reserve("C12", 12_000) }
            .isExactlyInstanceOf(BookingUnavailableException::class.java)
            .hasMessage("booking service timed out")
        assertThat(script.reserveCalls.get()).isEqualTo(3)
        assertThat(log.calls().single().failed).isTrue()
    }

    @Test
    fun `does not retry a failure that is not listed`() {
        val c = app()
        val script = c.get(BookingScript::class.java)
        script.badSeat = true
        assertThatThrownBy { c.get(BookingClient::class.java).reserve("Z99", 500) }
            .isExactlyInstanceOf(IllegalArgumentException::class.java)
        assertThat(script.reserveCalls.get()).isEqualTo(1)
    }

    @Test
    fun `a default method's inner calls are intercepted and retried one by one`() {
        val c = app()
        val script = c.get(BookingScript::class.java)
        script.confirmFailures.set(1)
        assertThat(c.get(BookingClient::class.java).reserveAndConfirm("C12", 12_000))
            .isEqualTo("ticket-hold-C12")
        assertThat(script.reserveCalls.get()).`as`("seats held").isEqualTo(1)
        assertThat(script.confirmCalls.get()).`as`("confirmations sent").isEqualTo(2)
        assertThat(log.names()).containsExactly("BookingClient.reserve", "BookingClient.confirm")
    }

    @Test
    fun `a JDK proxy answers equals, hashCode and toString itself`() {
        val c = app()
        val booking = c.get(BookingClient::class.java)
        assertThat(Proxy.isProxyClass(booking.javaClass)).isTrue()
        assertThat(booking.equals(booking)).isTrue()
        val listeners = arrayListOf(booking)
        assertThat(listeners.remove(booking)).`as`("ArrayList.remove uses equals").isTrue()
        assertThat(booking.hashCode()).isEqualTo(System.identityHashCode(booking))
        assertThat(booking.toString()).contains("FakeBooking")
        assertThat(c.get(BookingClient::class.java)).isSameAs(booking)
        assertThat(booking.equals(app().get(BookingClient::class.java))).`as`("another container's proxy").isFalse()
        assertThat(log.calls()).`as`("Object methods are not timed").isEmpty()
    }

    @Test
    fun `asking for the class behind a JDK proxy names the interface to ask for`() {
        assertThatThrownBy { app().get(FakeBooking::class.java) }
            .isInstanceOf(ContainerException::class.java)
            .hasMessageContaining("FakeBooking is behind a JDK proxy")
            .hasMessageContaining("BookingClient")
    }

    @Test
    fun `a class without an interface gets a subclass, and its self-calls are intercepted`() {
        val c = app()
        val closer = c.get(ShowCloser::class.java)
        assertThat(closer.javaClass).isNotEqualTo(ShowCloser::class.java)
        assertThat(closer.javaClass.superclass).isEqualTo(ShowCloser::class.java)
        assertThat(closer.close("N-17")).isEqualTo("closed N-17")
        assertThat(log.names()).containsExactly("ShowCloser.verify", "ShowCloser.close")
        assertThat(closer.hall()).isEqualTo("Main hall")
        assertThat(c.get(ShowArchive::class.java).filed()).containsExactly("N-17")
        assertThat(c.get(ShowCloser::class.java)).isSameAs(closer)
    }

    @Test
    fun `retry works on a subclass too`() {
        val fetcher = app().get(ReviewFetcher::class.java)
        assertThat(fetcher.fetch()).isEqualTo("4 stars")
        assertThat(fetcher.calls.get()).isEqualTo(3)
    }

    @Test
    fun `a final class with an intercepted method is refused when the container starts`() {
        assertThatThrownBy { Container(listOf(FrozenPrices::class.java)) }
            .isInstanceOf(ContainerException::class.java)
            .hasMessage("FrozenPrices is final, so no subclass can intercept it: make it open, or give it an interface")
    }

    @Test
    fun `an intercepted method left final is refused too`() {
        assertThatThrownBy { Container(listOf(HalfOpen::class.java)) }
            .isInstanceOf(ContainerException::class.java)
            .hasMessage("HalfOpen.hall is final, so no subclass can intercept it: make it open")
    }

    @Test
    fun `annotations a JDK proxy would never see are refused`() {
        assertThatThrownBy { Container(listOf(MisplacedTimed::class.java)) }
            .isInstanceOf(ContainerException::class.java)
            .hasMessageContaining("MisplacedTimed.ping")
            .hasMessageContaining("Pinger")
    }

    @Test
    fun `a final class with nothing to intercept is created as it is`() {
        val plain = app().get(PlainFinal::class.java)
        assertThat(plain.javaClass).isEqualTo(PlainFinal::class.java)
        assertThat(plain.hello()).isEqualTo("hi")
    }
}
