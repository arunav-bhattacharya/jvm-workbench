package workbench.events.l01

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatCode
import org.assertj.core.api.Assertions.assertThatIllegalArgumentException
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import kotlin.reflect.KClass

class ModelTest {
    private val id = PaymentId("pay_7781")

    private fun rejected(fields: Map<String, String>): String {
        val result = parseEvent(fields)
        assertThat(result).`as`("parseEvent($fields)").isInstanceOf(Parsed.Rejected::class.java)
        return (result as Parsed.Rejected).reason
    }

    // ---- value classes ----

    @Test
    fun `a payment id is pay_ followed by 4 to 24 letters or digits`() {
        assertThat(PaymentId("pay_7781").value).isEqualTo("pay_7781")
        assertThat(PaymentId("pay_AbC123xyz").value).isEqualTo("pay_AbC123xyz")
        for (bad in listOf("7781", "pay_", "pay_77", "PAY_7781", "pay_7781!", " pay_7781", "pay_" + "1".repeat(25))) {
            assertThatIllegalArgumentException().`as`("PaymentId(\"$bad\")")
                .isThrownBy { PaymentId(bad) }
                .withMessageContaining(bad)
        }
    }

    @Test
    fun `money is never negative`() {
        assertThat(Money(0).minor).isZero()
        assertThatIllegalArgumentException().isThrownBy { Money(-1) }.withMessageContaining("-1")
    }

    @Test
    fun `money adds and subtracts exactly`() {
        assertThat(Money(1_999) + Money(1)).isEqualTo(Money(2_000))
        assertThat(Money(1_999) - Money(999)).isEqualTo(Money(1_000))
        assertThatIllegalArgumentException().`as`("5.00 - 5.01").isThrownBy { Money(500) - Money(501) }
        assertThatThrownBy { Money(Long.MAX_VALUE) + Money(1) }.isInstanceOf(ArithmeticException::class.java)
    }

    @Test
    fun `money prints as euros with two decimals`() {
        assertThat(Money(1_999).toString()).isEqualTo("19.99")
        assertThat(Money(5).toString()).isEqualTo("0.05")
    }

    @Test
    fun `authorized, captured and refunded amounts must be positive`() {
        assertThatIllegalArgumentException().isThrownBy { PaymentAuthorized(id, Money.ZERO) }
        assertThatIllegalArgumentException().isThrownBy { PaymentCaptured(id, Money.ZERO) }
        assertThatIllegalArgumentException().isThrownBy { PaymentRefunded(id, Money.ZERO) }
        assertThat(PaymentCaptured(id, Money(1)).amount).isEqualTo(Money(1))
    }

    // ---- the edge ----

    @Test
    fun `parse builds each event type from valid fields`() {
        assertThat(parseEvent(mapOf("type" to "authorized", "paymentId" to "pay_7781", "amountMinor" to "1999")))
            .isEqualTo(Parsed.Ok(PaymentAuthorized(id, Money(1_999))))
        assertThat(parseEvent(mapOf("type" to "captured", "paymentId" to "pay_7781", "amountMinor" to "1999")))
            .isEqualTo(Parsed.Ok(PaymentCaptured(id, Money(1_999))))
        assertThat(parseEvent(mapOf("type" to "refunded", "paymentId" to "pay_7781", "amountMinor" to "500")))
            .isEqualTo(Parsed.Ok(PaymentRefunded(id, Money(500))))
        assertThat(parseEvent(mapOf("type" to "declined", "paymentId" to "pay_7781", "reason" to "CARD_EXPIRED")))
            .isEqualTo(Parsed.Ok(PaymentDeclined(id, DeclineReason.CARD_EXPIRED)))
    }

    @Test
    fun `parse names the field that is missing`() {
        assertThat(rejected(mapOf("paymentId" to "pay_7781", "amountMinor" to "1999"))).contains("type")
        assertThat(rejected(mapOf("type" to "captured", "amountMinor" to "1999"))).contains("paymentId")
        assertThat(rejected(mapOf("type" to "captured", "paymentId" to "pay_7781"))).contains("amountMinor")
        assertThat(rejected(mapOf("type" to "declined", "paymentId" to "pay_7781"))).contains("reason")
    }

    @Test
    fun `parse rejects amounts that are not whole numbers of cents`() {
        for (raw in listOf("12.50", "1e3", "", " 1999", "19,99", "99999999999999999999")) {
            assertThat(rejected(mapOf("type" to "captured", "paymentId" to "pay_7781", "amountMinor" to raw)))
                .`as`("amountMinor '$raw'").contains("amountMinor")
        }
    }

    @Test
    fun `parse turns a constructor's refusal into Rejected`() {
        assertThat(rejected(mapOf("type" to "captured", "paymentId" to "7781", "amountMinor" to "1999"))).contains("7781")
        assertThat(rejected(mapOf("type" to "refunded", "paymentId" to "pay_7781", "amountMinor" to "-500"))).contains("-500")
        assertThat(rejected(mapOf("type" to "captured", "paymentId" to "pay_7781", "amountMinor" to "0"))).contains("positive")
    }

    @Test
    fun `parse rejects unknown event types and decline reasons by name`() {
        assertThat(rejected(mapOf("type" to "chargeback", "paymentId" to "pay_7781", "amountMinor" to "1999"))).contains("chargeback")
        assertThat(rejected(mapOf("type" to "declined", "paymentId" to "pay_7781", "reason" to "stolen"))).contains("stolen")
    }

    @Test
    fun `parse never throws, whatever arrives`() {
        val hostile = listOf(
            emptyMap(),
            mapOf("type" to ""),
            mapOf("type" to "CAPTURED", "paymentId" to "pay_7781", "amountMinor" to "1"),
            mapOf("type" to "captured", "paymentId" to "", "amountMinor" to ""),
            mapOf("type" to "declined", "paymentId" to "pay_7781", "reason" to "card_expired"),
            mapOf("type" to "refunded", "paymentId" to "pay_7781", "amountMinor" to "-9223372036854775808"),
            mapOf("type" to "authorized", "paymentId" to "pay_\u0000\u0000\u0000\u0000", "amountMinor" to "1"),
        )
        for (fields in hostile) {
            assertThatCode { assertThat(parseEvent(fields)).isInstanceOf(Parsed.Rejected::class.java) }
                .`as`("parseEvent($fields)").doesNotThrowAnyException()
        }
    }

    // ---- exhaustive operations ----

    private val samples: List<PaymentEvent> = listOf(
        PaymentAuthorized(id, Money(1_999)),
        PaymentDeclined(id, DeclineReason.SUSPECTED_FRAUD),
        PaymentCaptured(id, Money(1_999)),
        PaymentRefunded(id, Money(500)),
    )

    private fun leaves(type: KClass<*>): Set<KClass<*>> =
        if (type.isSealed) type.sealedSubclasses.flatMap(::leaves).toSet() else setOf(type)

    @Test
    fun `every event type has a summary line`() {
        // if this first check fails, someone added an event type: add a sample for it above
        assertThat(samples.map { it::class }.toSet()).isEqualTo(leaves(PaymentEvent::class))
        assertThat(samples.map(::summary)).containsExactly(
            "pay_7781 authorized 19.99 EUR",
            "pay_7781 declined: SUSPECTED_FRAUD",
            "pay_7781 captured 19.99 EUR",
            "pay_7781 refunded 5.00 EUR",
        )
    }
}
