package workbench.generics.l10

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.math.BigDecimal

class AdvancedTest {

    @Test
    fun `a card payment chain keeps the subclass type through the base setters`() {
        val payment = CardPaymentBuilder()
            .amount(1_200)          // returns CardPaymentBuilder, not the base class
            .currency("EUR")
            .cardToken("tok_42")    // so this subclass method is still reachable
            .reference("order 7")
            .build()
        assertThat(payment).isEqualTo(CardPayment(1_200, "EUR", "order 7", "tok_42"))
    }

    @Test
    fun `a bank transfer uses the same base setters and its own iban`() {
        val transfer = BankTransferBuilder().iban("NL91ABNA0417164300").currency("EUR").amount(9_900).build()
        assertThat(transfer).isEqualTo(BankTransfer(9_900, "EUR", "", "NL91ABNA0417164300"))
    }

    @Test
    fun `build checks the common fields first`() {
        assertThatThrownBy { CardPaymentBuilder().currency("EUR").cardToken("tok_1").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("amount must be positive")
        assertThatThrownBy { BankTransferBuilder().amount(10).iban("NL00").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("currency is required")
    }

    @Test
    fun `build checks the subclass fields`() {
        assertThatThrownBy { CardPaymentBuilder().amount(10).currency("EUR").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("card token is required")
        assertThatThrownBy { BankTransferBuilder().amount(10).currency("EUR").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("iban is required")
    }

    @Test
    fun `andThen composes, and accepts a more general second function`() {
        val parseCents: (String) -> Long = { BigDecimal(it).movePointRight(2).longValueExact() }
        val describe: (Any) -> String = { "<$it>" }              // takes Any, not just Long
        val f: (String) -> CharSequence = andThen(parseCents, describe)   // and the result is used as CharSequence
        assertThat(f("12.50").toString()).isEqualTo("<1250>")
    }

    @Test
    fun `andThen runs first before second, once each`() {
        val calls = mutableListOf<String>()
        val f = andThen<Int, Int, Int>({ calls += "first"; it + 1 }, { calls += "second"; it * 10 })
        assertThat(f(4)).isEqualTo(50)
        assertThat(calls).containsExactly("first", "second")
    }

    @Test
    fun `fanOut calls every handler in order, including handlers for a supertype`() {
        val log = mutableListOf<String>()
        val audit: Handler<PaymentEvent> = { log += "audit ${it.paymentId}" }
        val fraud: Handler<CardAuthorized> = { log += "fraud ${it.cents}" }
        val all: Handler<CardAuthorized> = fanOut(listOf(audit, fraud))   // a Handler<PaymentEvent> fits: in P
        all(CardAuthorized("pay_1", 1_200))
        assertThat(log).containsExactly("audit pay_1", "fraud 1200")
    }

    @Test
    fun `firstNotNullValue skips nulls and returns a non-null type`() {
        val code: String = listOf(null, "EUR", "USD").firstNotNullValue()   // T = String?, result String
        assertThat(code).isEqualTo("EUR")
        assertThatThrownBy { listOf<String?>(null, null).firstNotNullValue() }
            .isInstanceOf(NoSuchElementException::class.java).hasMessage("no non-null element")
        assertThatThrownBy { emptyList<Int>().firstNotNullValue() }
            .isInstanceOf(NoSuchElementException::class.java)
    }
}
