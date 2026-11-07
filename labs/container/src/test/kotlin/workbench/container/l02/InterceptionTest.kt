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
        listOf(IssuerScript::class.java, FakeIssuer::class.java, SettlementLedger::class.java,
            SettlementService::class.java, RatesFetcher::class.java, PlainFinal::class.java),
        Interception(log, clock),
    )

    @Test
    fun `retries authorize until the issuer answers, and times the call once`() {
        val c = app()
        val script = c.get(IssuerScript::class.java)
        script.authorizeFailures.set(2)
        assertThat(c.get(CardIssuerClient::class.java).authorize("4111111111111111", 12_000)).isEqualTo("auth-1111")
        assertThat(script.authorizeCalls.get()).`as`("calls the issuer saw").isEqualTo(3)
        assertThat(log.calls()).containsExactly(Call("CardIssuerClient.authorize", 1_000_000, false))
    }

    @Test
    fun `gives up after the last attempt and rethrows the issuer's own exception`() {
        val c = app()
        val script = c.get(IssuerScript::class.java)
        script.authorizeFailures.set(5)
        assertThatThrownBy { c.get(CardIssuerClient::class.java).authorize("4111111111111111", 12_000) }
            .isExactlyInstanceOf(IssuerUnavailableException::class.java)
            .hasMessage("issuer timed out")
        assertThat(script.authorizeCalls.get()).isEqualTo(3)
        assertThat(log.calls().single().failed).isTrue()
    }

    @Test
    fun `does not retry a failure that is not listed`() {
        val c = app()
        val script = c.get(IssuerScript::class.java)
        script.badCard = true
        assertThatThrownBy { c.get(CardIssuerClient::class.java).authorize("4111111111111112", 500) }
            .isExactlyInstanceOf(IllegalArgumentException::class.java)
        assertThat(script.authorizeCalls.get()).isEqualTo(1)
    }

    @Test
    fun `a default method's inner calls are intercepted and retried one by one`() {
        val c = app()
        val script = c.get(IssuerScript::class.java)
        script.captureFailures.set(1)
        assertThat(c.get(CardIssuerClient::class.java).authorizeAndCapture("4111111111111111", 12_000))
            .isEqualTo("cap-auth-1111")
        assertThat(script.authorizeCalls.get()).`as`("authorizations sent").isEqualTo(1)
        assertThat(script.captureCalls.get()).`as`("captures sent").isEqualTo(2)
        assertThat(log.names()).containsExactly("CardIssuerClient.authorize", "CardIssuerClient.capture")
    }

    @Test
    fun `a JDK proxy answers equals, hashCode and toString itself`() {
        val c = app()
        val issuer = c.get(CardIssuerClient::class.java)
        assertThat(Proxy.isProxyClass(issuer.javaClass)).isTrue()
        assertThat(issuer.equals(issuer)).isTrue()
        val listeners = arrayListOf(issuer)
        assertThat(listeners.remove(issuer)).`as`("ArrayList.remove uses equals").isTrue()
        assertThat(issuer.hashCode()).isEqualTo(System.identityHashCode(issuer))
        assertThat(issuer.toString()).contains("FakeIssuer")
        assertThat(c.get(CardIssuerClient::class.java)).isSameAs(issuer)
        assertThat(issuer.equals(app().get(CardIssuerClient::class.java))).`as`("another container's proxy").isFalse()
        assertThat(log.calls()).`as`("Object methods are not timed").isEmpty()
    }

    @Test
    fun `asking for the class behind a JDK proxy names the interface to ask for`() {
        assertThatThrownBy { app().get(FakeIssuer::class.java) }
            .isInstanceOf(ContainerException::class.java)
            .hasMessageContaining("FakeIssuer is behind a JDK proxy")
            .hasMessageContaining("CardIssuerClient")
    }

    @Test
    fun `a class without an interface gets a subclass, and its self-calls are intercepted`() {
        val c = app()
        val settlement = c.get(SettlementService::class.java)
        assertThat(settlement.javaClass).isNotEqualTo(SettlementService::class.java)
        assertThat(settlement.javaClass.superclass).isEqualTo(SettlementService::class.java)
        assertThat(settlement.settle("B-17")).isEqualTo("settled B-17")
        assertThat(log.names()).containsExactly("SettlementService.audit", "SettlementService.settle")
        assertThat(settlement.region()).isEqualTo("EU")
        assertThat(c.get(SettlementLedger::class.java).posted()).containsExactly("B-17")
        assertThat(c.get(SettlementService::class.java)).isSameAs(settlement)
    }

    @Test
    fun `retry works on a subclass too`() {
        val fetcher = app().get(RatesFetcher::class.java)
        assertThat(fetcher.fetch()).isEqualTo("EUR/USD 1.0870")
        assertThat(fetcher.calls.get()).isEqualTo(3)
    }

    @Test
    fun `a final class with an intercepted method is refused when the container starts`() {
        assertThatThrownBy { Container(listOf(FrozenFees::class.java)) }
            .isInstanceOf(ContainerException::class.java)
            .hasMessage("FrozenFees is final, so no subclass can intercept it: make it open, or give it an interface")
    }

    @Test
    fun `an intercepted method left final is refused too`() {
        assertThatThrownBy { Container(listOf(HalfOpen::class.java)) }
            .isInstanceOf(ContainerException::class.java)
            .hasMessage("HalfOpen.region is final, so no subclass can intercept it: make it open")
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
