package workbench.functional.l07

import arrow.core.Either
import arrow.core.left
import arrow.core.nonEmptyListOf
import arrow.core.right
import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.test.advanceTimeBy
import kotlinx.coroutines.test.runTest
import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import java.io.IOException

@OptIn(ExperimentalCoroutinesApi::class)
class ErrorsAsValuesTest {

    private val good = PaymentRequest(4_250, "EUR", "4111111111111111", "Order 981, Acme Books")

    // ---- validate: collect every error ----

    @Test
    fun `validate accepts a good request`() {
        assertThat(validate(good)).isEqualTo(ValidPayment(4_250, "EUR", "4111111111111111", "Order 981, Acme Books").right())
    }

    @Test
    fun `validate reports one broken rule`() {
        assertThat(validate(good.copy(currency = "XYZ")))
            .isEqualTo(nonEmptyListOf<PaymentError>(PaymentError.UnsupportedCurrency("XYZ")).left())
    }

    @Test
    fun `validate reports every broken rule at once, in order`() {
        val bad = PaymentRequest(-5, "XYZ", "41111111111x1234", "x".repeat(40))
        assertThat(validate(bad)).isEqualTo(
            nonEmptyListOf(
                PaymentError.InvalidAmount(-5),
                PaymentError.UnsupportedCurrency("XYZ"),
                PaymentError.InvalidCardNumber("1234"),
                PaymentError.ReferenceTooLong(40),
            ).left()
        )
    }

    @Test
    fun `validate checks the card number length and the reference length`() {
        assertThat(validate(good.copy(cardNumber = "411111111111111"))) // 15 digits
            .isEqualTo(nonEmptyListOf<PaymentError>(PaymentError.InvalidCardNumber("1111")).left())
        assertThat(validate(good.copy(reference = "r".repeat(35))).isRight()).`as`("35 characters is allowed").isTrue()
    }

    // ---- pay: fail fast ----

    private val valid = ValidPayment(4_250, "EUR", "4111111111111111", "Order 981")

    private class FakeGateway(
        private val auth: Either<PaymentError, String> = "A-1".right(),
        private val score: Int = 12,
        private val capture: Either<PaymentError, String> = "C-1".right(),
    ) : Gateway {
        val calls = mutableListOf<String>()
        override fun authorize(payment: ValidPayment) = auth.also { calls += "authorize" }
        override fun riskScore(authCode: String) = score.also { calls += "riskScore" }
        override fun capture(authCode: String) = capture.also { calls += "capture" }
    }

    @Test
    fun `pay returns a receipt when every step succeeds`() {
        val gateway = FakeGateway()
        assertThat(pay(valid, gateway)).isEqualTo(Receipt("A-1", "C-1").right())
        assertThat(gateway.calls).containsExactly("authorize", "riskScore", "capture")
    }

    @Test
    fun `pay stops at a declined authorization`() {
        val gateway = FakeGateway(auth = PaymentError.CardDeclined.left())
        assertThat(pay(valid, gateway)).isEqualTo(PaymentError.CardDeclined.left())
        assertThat(gateway.calls).containsExactly("authorize")
    }

    @Test
    fun `pay refuses a high fraud score and never captures`() {
        val gateway = FakeGateway(score = 91)
        assertThat(pay(valid, gateway)).isEqualTo(PaymentError.FraudSuspected(91).left())
        assertThat(gateway.calls).containsExactly("authorize", "riskScore")
    }

    @Test
    fun `pay treats the threshold itself as fraud`() {
        assertThat(pay(valid, FakeGateway(score = FRAUD_THRESHOLD))).isEqualTo(PaymentError.FraudSuspected(80).left())
        assertThat(pay(valid, FakeGateway(score = FRAUD_THRESHOLD - 1)).isRight()).isTrue()
    }

    @Test
    fun `pay returns a failed capture as it is`() {
        val gateway = FakeGateway(capture = PaymentError.ProviderUnavailable.left())
        assertThat(pay(valid, gateway)).isEqualTo(PaymentError.ProviderUnavailable.left())
    }

    // ---- runCatchingCancellable ----

    @Test
    fun `runCatchingCancellable wraps a value`() = runTest {
        assertThat(runCatchingCancellable { delay(100); "auth-1" }).isEqualTo(Result.success("auth-1"))
    }

    @Test
    fun `runCatchingCancellable wraps an ordinary exception`() = runTest {
        val result = runCatchingCancellable<String> { delay(100); throw IOException("issuer timeout") }
        assertThat(result.exceptionOrNull()).isInstanceOf(IOException::class.java).hasMessage("issuer timeout")
    }

    @Test
    fun `a cancelled caller does not carry on after runCatchingCancellable`() = runTest {
        val ledger = mutableListOf<String>()
        val payment = launch {
            val result = runCatchingCancellable { delay(1_000); "auth-1" }
            ledger += "charged card ($result)"     // must never run once the payment is cancelled
        }
        advanceTimeBy(50)
        payment.cancelAndJoin()
        assertThat(ledger).`as`("ledger writes after the cancel").isEmpty()
        assertThat(payment.isCancelled).isTrue()
    }
}
