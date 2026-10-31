package workbench.patterns.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class PaymentDslTest {

    @Test
    fun `the DSL builds a request whose total is the sum of its items`() {
        val req = paymentRequest {
            idempotencyKey = "order-981-attempt-1"
            lineItems {
                item("sku-1", 1_000)
                item("sku-2", 500)
            }
            metadata("orderId", "981")
        }
        assertThat(req.idempotencyKey).isEqualTo("order-981-attempt-1")
        assertThat(req.currency).isEqualTo("EUR")
        assertThat(req.lineItems).containsExactly(LineItem("sku-1", 1_000), LineItem("sku-2", 500))
        assertThat(req.amountMinor).isEqualTo(1_500)
        assertThat(req.metadata).containsExactlyEntriesOf(mapOf("orderId" to "981"))
    }

    @Test
    fun `two lineItems blocks add up, and a repeated metadata key keeps the last value`() {
        val req = paymentRequest {
            idempotencyKey = "k-2"
            currency = "SEK"
            lineItems { item("a", 100) }
            lineItems { item("b", 200); item("c", 300) }
            metadata("channel", "web")
            metadata("channel", "app")
        }
        assertThat(req.lineItems.map { it.sku }).containsExactly("a", "b", "c")
        assertThat(req.amountMinor).isEqualTo(600)
        assertThat(req.currency).isEqualTo("SEK")
        assertThat(req.metadata).containsExactlyEntriesOf(mapOf("channel" to "app"))
    }

    @Test
    fun `build rejects a missing or blank idempotency key`() {
        assertThatThrownBy { paymentRequest { lineItems { item("a", 100) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("idempotency key")
        assertThatThrownBy { paymentRequest { idempotencyKey = "  "; lineItems { item("a", 100) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("idempotency key")
    }

    @Test
    fun `build rejects a currency that is not three capital letters`() {
        for (bad in listOf("eur", "EURO", "E1R", "")) {
            assertThatThrownBy { paymentRequest { idempotencyKey = "k"; currency = bad; lineItems { item("a", 1) } } }
                .`as`("currency '$bad'")
                .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("currency")
        }
    }

    @Test
    fun `build rejects no items, and items with a zero or negative amount`() {
        assertThatThrownBy { paymentRequest { idempotencyKey = "k" } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("line item")
        assertThatThrownBy { paymentRequest { idempotencyKey = "k"; lineItems { item("free", 0) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("line item")
        assertThatThrownBy { paymentRequest { idempotencyKey = "k"; lineItems { item("a", 100); item("refund?", -50) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("line item")
    }

    @Test
    fun `a built request does not change when the builder is used again`() {
        val builder = PaymentRequestBuilder().apply {
            idempotencyKey = "k-3"
            lineItems { item("a", 100) }
            metadata("m", "1")
        }
        val first = builder.build()
        builder.lineItems { item("b", 200) }
        builder.metadata("m", "2")
        val second = builder.build()
        assertThat(first.lineItems).hasSize(1)
        assertThat(first.metadata).containsEntry("m", "1")
        assertThat(second.lineItems).hasSize(2)
    }

    @Test
    fun `LineItemsBuilder hands out a copy of its items`() {
        val b = LineItemsBuilder()
        b.item("a", 1)
        val snapshot = b.build()
        b.item("b", 2)
        assertThat(snapshot).hasSize(1)
    }

    @Test
    fun `both builder classes are marked with PaymentDsl`() {
        // the compiler enforces the scope rule; this only checks that you put the marker on both builders
        for (cls in listOf(PaymentRequestBuilder::class.java, LineItemsBuilder::class.java)) {
            assertThat(cls.isAnnotationPresent(PaymentDsl::class.java)).`as`("@PaymentDsl on ${cls.simpleName}").isTrue()
        }
    }
}
