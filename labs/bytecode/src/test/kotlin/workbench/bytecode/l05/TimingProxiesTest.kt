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

    private fun subclass() = TimingProxies.subclassTimed(FxQuoteService::class.java, ticking(), sink)

    @Test
    fun `subclassTimed returns a generated subclass that still computes the right quote`() {
        val fx = subclass()
        assertThat(fx.javaClass.name).contains("\$ByteBuddy\$")
        assertThat(fx.javaClass.superclass).isEqualTo(FxQuoteService::class.java)
        assertThat(fx.quote("EURUSD", 100_000)).isEqualTo(108_575)   // 108,425 + 150 spread
    }

    @Test
    fun `in the subclass model, calls on this are intercepted too`() {
        subclass().quote("EURUSD", 100_000)
        assertThat(records).containsExactly(
            "FxQuoteService.rateMicros 1ms",
            "FxQuoteService.spreadMinor 1ms",
            "FxQuoteService.quote 5ms",
        )
    }

    @Test
    fun `an exception reaches the caller unchanged and is recorded as failed`() {
        val fx = subclass()
        assertThatThrownBy { fx.rateMicros("XAUUSD") }
            .isExactlyInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("unknown pair XAUUSD")
        assertThat(records).containsExactly("FxQuoteService.rateMicros 1ms FAILED")
    }

    @Test
    fun `a final method is not intercepted`() {
        val fx = subclass()
        assertThat(fx.deskName()).isEqualTo("desk unset")
        assertThat(records).isEmpty()
    }

    @Test
    fun `in the forwarding model, only the outer call is timed`() {
        val target = FxQuoteService()
        val fx = TimingProxies.forwardingTimed(FxQuoteService::class.java, target, ticking(), sink)
        assertThat(fx.quote("GBPUSD", 100_000)).isEqualTo(127_190)   // 127,040 + 150 spread
        assertThat(records).containsExactly("FxQuoteService.quote 1ms")
    }

    @Test
    fun `a forwarding proxy sends open methods to the target but runs final methods on itself`() {
        val target = FxQuoteService().apply { desk = "London" }
        val fx = TimingProxies.forwardingTimed(FxQuoteService::class.java, target, ticking(), sink)
        assertThat(fx.desk).describedAs("desk is a final property: read from the proxy's own field").isEqualTo("unset")
        assertThat(fx.deskName()).describedAs("final method: runs on the proxy object").isEqualTo("desk unset")
        assertThat(fx.rateMicros("EURUSD")).isEqualTo(1_084_250)
        assertThat(records).containsExactly("FxQuoteService.rateMicros 1ms")
    }
}
