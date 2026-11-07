package workbench.generics.l08

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.math.BigDecimal
import java.time.LocalDate
import java.util.UUID

class ReifiedTest {
    private val auth = CardAuthorized("pay_1", 1_200)
    private val refund = RefundIssued("pay_2", 500)

    @Test
    fun `asOrNull returns the value when it has the requested type`() {
        assertThat(Callers.stringOrNull("EUR")).isEqualTo("EUR")
        assertThat(Callers.longOrNull(1_200L)).isEqualTo(1_200L)
        assertThat(Callers.eventOrNull(refund)).isEqualTo(refund)
    }

    @Test
    fun `asOrNull returns null for a value of another type, and for null`() {
        // with an erased T these calls would not return null: they would throw ClassCastException in Callers
        assertThat(Callers.stringOrNull(42)).isNull()
        assertThat(Callers.longOrNull("1200")).isNull()
        assertThat(Callers.eventOrNull("pay_1")).isNull()
        assertThat(Callers.stringOrNull(null)).isNull()
    }

    @Test
    fun `instancesOf keeps the elements of the requested type, in order`() {
        val auth2 = CardAuthorized("pay_3", 99)
        assertThat(Callers.cardsIn(listOf(auth, refund, "pay_x", auth2, null))).containsExactly(auth, auth2)
        assertThat(Callers.stringsIn(listOf(1, "EUR", null, 2.5, "USD"))).containsExactly("EUR", "USD")
        assertThat(Callers.stringsIn(emptyList())).isEmpty()
    }

    @Test
    fun `parse with a reified type finds the parser registered for that class`() {
        val parsers = Parsers()
        parsers.register(Money::class.java) { Money.parse(it) }
        parsers.register(LocalDate::class.java) { LocalDate.parse(it) }
        assertThat(Callers.money(parsers, "12.50 EUR")).isEqualTo(Money(1_250, "EUR"))
        assertThat(Callers.date(parsers, "2026-03-01")).isEqualTo(LocalDate.of(2026, 3, 1))
    }

    @Test
    fun `parse with a Class token works the same way`() {
        val parsers = Parsers()
        parsers.register(BigDecimal::class.java) { BigDecimal(it) }
        assertThat(parsers.parse("0.25", BigDecimal::class.java)).isEqualByComparingTo("0.25")
    }

    @Test
    fun `parse of a type with no parser throws IllegalArgumentException naming the type`() {
        val parsers = Parsers()
        assertThatThrownBy { parsers.parse("x", UUID::class.java) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("no parser for UUID")
        assertThatThrownBy { Callers.money(parsers, "1.00 EUR") }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("no parser for Money")
    }
}
