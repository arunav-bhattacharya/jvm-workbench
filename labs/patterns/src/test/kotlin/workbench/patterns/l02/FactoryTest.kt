package workbench.patterns.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class FactoryTest {

    private fun valid(raw: String): Card {
        val r = Card.parse(raw)
        assertThat(r).`as`("parse(\"$raw\")").isInstanceOf(CardResult.Valid::class.java)
        return (r as CardResult.Valid).card
    }

    private fun reason(raw: String): String {
        val r = Card.parse(raw)
        assertThat(r).`as`("parse(\"$raw\")").isInstanceOf(CardResult.Invalid::class.java)
        return (r as CardResult.Invalid).reason
    }

    @Test
    fun `a Visa number with spaces parses to a Visa card`() {
        val card = valid("4111 1111 1111 1111")
        assertThat(card.network).isEqualTo(Network.VISA)
        assertThat(card.last4).isEqualTo("1111")
    }

    @Test
    fun `51 to 55 and 2221 to 2720 prefixes are Mastercard`() {
        assertThat(valid("5555 5555 5555 4444").network).isEqualTo(Network.MASTERCARD)
        assertThat(valid("5105105105105100").network).isEqualTo(Network.MASTERCARD)
        assertThat(valid("2223003122003222").network).isEqualTo(Network.MASTERCARD)
        assertThat(valid("2223003122003222").last4).isEqualTo("3222")
    }

    @Test
    fun `bad input comes back as Invalid with a reason, in the documented order`() {
        assertThat(reason("4111-1111-1111-1111")).isEqualTo("digits only")
        assertThat(reason("4111 1111")).isEqualTo("length")
        assertThat(reason("")).isEqualTo("length")
        assertThat(reason("4111 1111 1111 1112")).isEqualTo("checksum")
        assertThat(reason("378282246310005")).`as`("an Amex test number").isEqualTo("unsupported network")
        assertThat(reason("6011111111111117")).`as`("a Discover test number").isEqualTo("unsupported network")
    }

    @Test
    fun `every network has a sandbox family that reports its own network`() {
        for (n in Network.entries) {
            assertThat(CardNetworkClients.sandbox(n).network).isEqualTo(n)
        }
        assertThat(CardNetworkClients.sandbox(Network.VISA).baseUrl).isEqualTo("https://sandbox.visa.example")
        assertThat(CardNetworkClients.sandbox(Network.MASTERCARD).baseUrl).isEqualTo("https://sandbox.mastercard.example")
    }

    @Test
    fun `a family's authorizer and refunder work together`() {
        val visa = CardNetworkClients.sandbox(Network.VISA)
        val auth = visa.authorizer().authorize(valid("4111 1111 1111 1111"), 1_250)
        assertThat(auth).isEqualTo("V-AUTH-1111-1250")
        assertThat(visa.refunder().refund(auth, 500)).isEqualTo("V-REFUND-500")

        val mc = CardNetworkClients.sandbox(Network.MASTERCARD)
        val mcAuth = mc.authorizer().authorize(valid("5555 5555 5555 4444"), 990)
        assertThat(mcAuth).isEqualTo("M-AUTH-4444-990")
        assertThat(mc.refunder().refund(mcAuth, 990)).isEqualTo("M-REFUND-990")
    }

    @Test
    fun `families refuse to mix networks`() {
        val visa = CardNetworkClients.sandbox(Network.VISA)
        val mc = CardNetworkClients.sandbox(Network.MASTERCARD)
        assertThatThrownBy { visa.authorizer().authorize(valid("5555 5555 5555 4444"), 100) }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { mc.refunder().refund("V-AUTH-1111-100", 100) }
            .isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `checkout pays through the family the factory returns for the card's network`() {
        val asked = mutableListOf<Network>()
        val checkout = Checkout { network -> asked += network; CardNetworkClients.sandbox(network) }
        assertThat(checkout.pay("2223 0031 2200 3222", 4_200)).isEqualTo(PayResult.Paid("M-AUTH-3222-4200"))
        assertThat(checkout.pay("4111 1111 1111 1111", 1_250)).isEqualTo(PayResult.Paid("V-AUTH-1111-1250"))
        assertThat(asked).containsExactly(Network.MASTERCARD, Network.VISA)
    }

    @Test
    fun `checkout rejects a bad number without ever calling the factory`() {
        var calls = 0
        val checkout = Checkout { network -> calls++; CardNetworkClients.sandbox(network) }
        assertThat(checkout.pay("4111 1111 1111 1112", 1_000)).isEqualTo(PayResult.Rejected("checksum"))
        assertThat(checkout.pay("3782 822463 10005", 1_000)).isEqualTo(PayResult.Rejected("unsupported network"))
        assertThat(calls).isZero()
    }

    @Test
    fun `checkout works with any factory, including a fake one`() {
        val fake = object : CardNetworkClients {
            override val network = Network.VISA
            override val baseUrl = "http://localhost:0"
            override fun authorizer() = Authorizer { card, amount -> "FAKE-${card.last4}-$amount" }
            override fun refunder() = Refunder { _, _ -> error("not used") }
        }
        assertThat(Checkout { fake }.pay("4242 4242 4242 4242", 7)).isEqualTo(PayResult.Paid("FAKE-4242-7"))
    }
}
