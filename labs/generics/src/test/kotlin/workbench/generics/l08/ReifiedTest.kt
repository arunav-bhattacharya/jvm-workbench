package workbench.generics.l08

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.math.BigDecimal
import java.time.LocalDate
import java.util.UUID

class ReifiedTest {
    private val gala = Apple("Gala", 180)
    private val eureka = Lemon("Eureka", 120)

    @Test
    fun `asOrNull returns the value when it has the requested type`() {
        assertThat(Callers.stringOrNull("Gala")).isEqualTo("Gala")
        assertThat(Callers.intOrNull(180)).isEqualTo(180)
        assertThat(Callers.fruitOrNull(eureka)).isEqualTo(eureka)
    }

    @Test
    fun `asOrNull returns null for a value of another type, and for null`() {
        // with an erased T these calls would not return null: they would throw ClassCastException in Callers
        assertThat(Callers.stringOrNull(42)).isNull()
        assertThat(Callers.intOrNull("180")).isNull()
        assertThat(Callers.fruitOrNull("Gala")).isNull()
        assertThat(Callers.stringOrNull(null)).isNull()
    }

    @Test
    fun `instancesOf keeps the elements of the requested type, in order`() {
        val fuji = Apple("Fuji", 150)
        assertThat(Callers.applesIn(listOf(gala, eureka, "a paper bag", fuji, null))).containsExactly(gala, fuji)
        assertThat(Callers.stringsIn(listOf(1, "Gala", null, 2.5, "Fuji"))).containsExactly("Gala", "Fuji")
        assertThat(Callers.stringsIn(emptyList())).isEmpty()
    }

    @Test
    fun `parse with a reified type finds the parser registered for that class`() {
        val parsers = Parsers()
        parsers.register(Weight::class.java) { Weight.parse(it) }
        parsers.register(LocalDate::class.java) { LocalDate.parse(it) }
        assertThat(Callers.weight(parsers, "1.25 kg")).isEqualTo(Weight(1_250))
        assertThat(Callers.date(parsers, "2026-03-01")).isEqualTo(LocalDate.of(2026, 3, 1))
    }

    @Test
    fun `parse with a Class token works the same way`() {
        val parsers = Parsers()
        parsers.register(BigDecimal::class.java) { BigDecimal(it) }
        assertThat(parsers.parse("2.40", BigDecimal::class.java)).isEqualByComparingTo("2.40")
    }

    @Test
    fun `parse of a type with no parser throws IllegalArgumentException naming the type`() {
        val parsers = Parsers()
        assertThatThrownBy { parsers.parse("x", UUID::class.java) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("no parser for UUID")
        assertThatThrownBy { Callers.weight(parsers, "180 g") }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("no parser for Weight")
    }
}
