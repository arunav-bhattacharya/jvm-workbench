package workbench.generics.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.time.LocalDate

class BoundsTest {
    // our own Comparable type: amounts compare by minor units (cents)
    private data class Money(val cents: Long) : Comparable<Money> {
        override fun compareTo(other: Money): Int = cents.compareTo(other.cents)
    }

    // a type that is BOTH a CharSequence and Comparable, so it fits the where clause
    private class MerchantCode(private val raw: String) : CharSequence by raw, Comparable<MerchantCode> {
        override fun compareTo(other: MerchantCode): Int = raw.compareTo(other.raw)
        override fun toString(): String = raw
    }

    @Test
    fun `maxOfAll works for any Comparable type`() {
        assertThat(maxOfAll(listOf(3, 41, 7))).isEqualTo(41)
        assertThat(maxOfAll(listOf("EUR", "USD", "GBP"))).isEqualTo("USD")
        assertThat(maxOfAll(listOf(Money(1_200), Money(99_000), Money(350)))).isEqualTo(Money(99_000))
        assertThat(maxOfAll(listOf(LocalDate.of(2026, 3, 1), LocalDate.of(2026, 1, 9)))).isEqualTo(LocalDate.of(2026, 3, 1))
    }

    @Test
    fun `maxOfAll of an empty list throws IllegalArgumentException`() {
        assertThatThrownBy { maxOfAll(emptyList<Int>()) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a Window contains its ends and what is between them`() {
        val amounts = Window(Money(1_000), Money(50_000))
        assertThat(Money(1_000) in amounts).isTrue()
        assertThat(Money(50_000) in amounts).isTrue()
        assertThat(Money(20_000) in amounts).isTrue()
        assertThat(Money(999) in amounts).isFalse()
        assertThat(Money(50_001) in amounts).isFalse()
    }

    @Test
    fun `clamp moves a value into the window`() {
        val days = Window(LocalDate.of(2026, 11, 2), LocalDate.of(2026, 11, 6))
        assertThat(days.clamp(LocalDate.of(2026, 10, 30))).isEqualTo(LocalDate.of(2026, 11, 2))
        assertThat(days.clamp(LocalDate.of(2026, 11, 9))).isEqualTo(LocalDate.of(2026, 11, 6))
        assertThat(days.clamp(LocalDate.of(2026, 11, 4))).isEqualTo(LocalDate.of(2026, 11, 4))
    }

    @Test
    fun `overlaps is true when windows share at least one value`() {
        val a = Window(10, 20)
        assertThat(a.overlaps(Window(20, 30))).isTrue()   // touch at 20
        assertThat(a.overlaps(Window(12, 15))).isTrue()   // inside
        assertThat(a.overlaps(Window(0, 9))).isFalse()
        assertThat(a.overlaps(Window(21, 25))).isFalse()
        assertThat(Window(0, 100).overlaps(a)).isTrue()
    }

    @Test
    fun `a Window whose start is after its end is rejected`() {
        assertThatThrownBy { Window("b", "a") }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `shortestLabel picks the shortest, then the smallest on a tie`() {
        assertThat(shortestLabel(listOf("SEPA", "ACH", "BACS", "CHAPS"))).isEqualTo("ACH")
        assertThat(shortestLabel(listOf("USD", "EUR", "GBPX"))).isEqualTo("EUR")
        val codes = listOf(MerchantCode("MC-0042"), MerchantCode("MC-7"), MerchantCode("MC-1"))
        assertThat(shortestLabel(codes).toString()).isEqualTo("MC-1")
    }

    @Test
    fun `coalesce returns the first non-null value, typed as non-null`() {
        val currency: String = coalesce(null, "EUR", "USD")   // String, not String?
        assertThat(currency).isEqualTo("EUR")
        assertThat(coalesce<Int>(null, null, 3)).isEqualTo(3)
    }

    @Test
    fun `coalesce of only nulls throws IllegalArgumentException`() {
        assertThatThrownBy { coalesce<String>(null, null) }.isInstanceOf(IllegalArgumentException::class.java)
    }
}
