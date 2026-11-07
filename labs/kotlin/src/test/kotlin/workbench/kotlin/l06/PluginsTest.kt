package workbench.kotlin.l06

import kotlinx.serialization.SerializationException
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonArray
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.jsonPrimitive
import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.lang.reflect.Modifier

class PluginsTest {

    private val events = listOf(
        Authorized("pay_1", 1_999),
        Captured("pay_1", 1_999),
        Refunded("pay_1", 500, "partial"),
    )

    @Test
    fun `events survive a round trip through JSON`() {
        assertThat(decodeEvents(encodeEvents(events))).isEqualTo(events)
    }

    @Test
    fun `each element carries a stable type discriminator`() {
        val types = Json.parseToJsonElement(encodeEvents(events)).jsonArray
            .map { it.jsonObject["type"]!!.jsonPrimitive.content }
        assertThat(types).containsExactly("authorized", "captured", "refunded")
    }

    @Test
    fun `defaults and nulls are left out of the JSON`() {
        val text = encodeEvents(listOf(Authorized("pay_2", 100), Refunded("pay_2", 100)))
        assertThat(text).doesNotContain("currency").doesNotContain("reason").doesNotContain("null")
        assertThat(decodeEvents(text)).containsExactly(Authorized("pay_2", 100, "EUR"), Refunded("pay_2", 100, null))
    }

    @Test
    fun `an unknown event type fails, an unknown key is ignored`() {
        assertThatThrownBy { decodeEvents("""[{"type":"chargeback","paymentId":"pay_3"}]""") }
            .isInstanceOf(SerializationException::class.java)
        assertThat(decodeEvents("""[{"type":"captured","paymentId":"pay_3","amountMinor":1,"acquirer":"acq-a"}]"""))
            .containsExactly(Captured("pay_3", 1))
    }

    @Test
    fun `FeeService is open, so a framework can generate a subclass proxy`() {
        val cls = FeeService::class.java
        assertThat(Modifier.isFinal(cls.modifiers)).`as`("class FeeService is final").isFalse()
        val fee = cls.getMethod("feeMinor", Long::class.javaPrimitiveType)
        assertThat(Modifier.isFinal(fee.modifiers)).`as`("feeMinor is final").isFalse()
        assertThat(FeeService().feeMinor(12_000)).isEqualTo(150)
    }

    @Test
    fun `PaymentEntity has a no-arg constructor for frameworks, and it skips the initializers`() {
        val cls = PaymentEntity::class.java
        assertThat(Modifier.isFinal(cls.modifiers)).`as`("class PaymentEntity is final").isFalse()
        val ctor = cls.getDeclaredConstructor()                    // what an ORM looks up
        val blank = ctor.newInstance()
        // invokeInitializers is off (the default), so the non-null String property was never set
        val note = cls.getDeclaredField("note").apply { isAccessible = true }.get(blank)
        assertThat(note).isNull()
        assertThat(PaymentEntity("pay_4", 10).note).isEqualTo("default-note")
    }
}
