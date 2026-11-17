package workbench.bytecode.l05

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.util.function.LongSupplier

class TimingProxiesTest {
    private val records = mutableListOf<String>()
    private val sink = TimingSink { m, nanos, failed -> records += "$m ${nanos / 1_000_000}ms" + if (failed) " FAILED" else "" }

    /** Every read moves time forward by 1 ms. */
    private fun ticking(): LongSupplier {
        var now = 0L
        return LongSupplier { now += 1_000_000; now }
    }

    private fun subclass() = TimingProxies.subclassTimed(BoxOffice::class.java, ticking(), sink)

    @Test
    fun `subclassTimed returns a generated subclass that still computes the right price`() {
        val office = subclass()
        assertThat(office.javaClass.name).contains("\$ByteBuddy\$")
        assertThat(office.javaClass.superclass).isEqualTo(BoxOffice::class.java)
        assertThat(office.price("stalls", 2)).isEqualTo(92)   // 2 x 45 + 2 booking fee
    }

    @Test
    fun `in the subclass model, calls on this are intercepted too`() {
        subclass().price("stalls", 2)
        assertThat(records).containsExactly(
            "BoxOffice.seatPrice 1ms",
            "BoxOffice.bookingFee 1ms",
            "BoxOffice.price 5ms",
        )
    }

    @Test
    fun `an exception reaches the caller unchanged and is recorded as failed`() {
        val office = subclass()
        assertThatThrownBy { office.seatPrice("balcony") }
            .isExactlyInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("unknown zone balcony")
        assertThat(records).containsExactly("BoxOffice.seatPrice 1ms FAILED")
    }

    @Test
    fun `a final method is not intercepted`() {
        val office = subclass()
        assertThat(office.welcome()).isEqualTo("welcome to unset")
        assertThat(records).isEmpty()
    }

    @Test
    fun `in the forwarding model, only the outer call is timed`() {
        val target = BoxOffice()
        val office = TimingProxies.forwardingTimed(BoxOffice::class.java, target, ticking(), sink)
        assertThat(office.price("circle", 3)).isEqualTo(99)   // 3 x 32 + 3 booking fee
        assertThat(records).containsExactly("BoxOffice.price 1ms")
    }

    @Test
    fun `a forwarding proxy sends open methods to the target but runs final methods on itself`() {
        val target = BoxOffice().apply { venue = "the Riverside" }
        val office = TimingProxies.forwardingTimed(BoxOffice::class.java, target, ticking(), sink)
        assertThat(office.venue).describedAs("venue is a final property: read from the proxy's own field").isEqualTo("unset")
        assertThat(office.welcome()).describedAs("final method: runs on the proxy object").isEqualTo("welcome to unset")
        assertThat(office.seatPrice("stalls")).isEqualTo(45)
        assertThat(records).containsExactly("BoxOffice.seatPrice 1ms")
    }
}
