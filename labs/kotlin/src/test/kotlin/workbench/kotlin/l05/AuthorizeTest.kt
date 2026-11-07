package workbench.kotlin.l05

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.catchThrowable
import org.junit.jupiter.api.Test

class AuthorizeTest {

    private val lines = mutableListOf<String>()
    private val log = AuditLog { lines += it }
    private val ok = AuthRequest(5_000, "eur", "tok_4242")

    @Test
    fun `ensure returns normally and never builds the message when the condition holds`() {
        var built = 0
        Callers.ensuring(true, "NEVER") { built++; "unused" }
        assertThat(built).isEqualTo(0)
    }

    @Test
    fun `ensure throws PaymentRejected with the code and message, building the message once`() {
        var built = 0
        val thrown = catchThrowable { Callers.ensuring(false, "OVER_LIMIT") { built++; "too much" } }
        assertThat(thrown).isInstanceOf(PaymentRejected::class.java).hasMessage("too much")
        assertThat((thrown as PaymentRejected).code).isEqualTo("OVER_LIMIT")
        assertThat(built).isEqualTo(1)
    }

    @Test
    fun `authorize approves within the limit and records one line with the transaction id`() {
        val decision = context(log, TxContext("tx-42")) { ok.authorize(limitMinor = 10_000) }
        assertThat(decision).isEqualTo(Decision.Approved)
        assertThat(lines).containsExactly("[tx-42] approved 5000 EUR")
    }

    @Test
    fun `authorize rejects over the limit and records why`() {
        val decision = context(log, TxContext("tx-43")) { ok.copy(amountMinor = 50_000).authorize(10_000) }
        assertThat(decision).isEqualTo(Decision.Rejected("OVER_LIMIT"))
        assertThat(lines).containsExactly("[tx-43] rejected OVER_LIMIT: amount 50000 is over the limit 10000")
    }

    @Test
    fun `authorize checks the rules in order and reports the first one that fails`() {
        context(log, TxContext("tx-44")) {
            assertThat(ok.copy(amountMinor = 0).authorize(10_000)).isEqualTo(Decision.Rejected("AMOUNT_INVALID"))
            assertThat(ok.copy(currency = null).authorize(10_000)).isEqualTo(Decision.Rejected("CURRENCY_MISSING"))
            assertThat(ok.copy(cardToken = "4242").authorize(10_000)).isEqualTo(Decision.Rejected("CARD_MISSING"))
            assertThat(ok.copy(currency = null, cardToken = null).authorize(10_000)).isEqualTo(Decision.Rejected("CURRENCY_MISSING"))
        }
        assertThat(lines).hasSize(4).allMatch { it.startsWith("[tx-44] rejected ") }
    }

    @Test
    fun `implicit receivers from with() also satisfy context parameters`() {
        val decision = with(log) { with(TxContext("tx-45")) { ok.authorize(10_000) } }
        assertThat(decision).isEqualTo(Decision.Approved)
        assertThat(lines).containsExactly("[tx-45] approved 5000 EUR")
    }
}
