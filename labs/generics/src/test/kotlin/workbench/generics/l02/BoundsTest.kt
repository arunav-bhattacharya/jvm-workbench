package workbench.generics.l02

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.time.LocalDate

class BoundsTest {
    // our own Comparable type: a weight in grams
    private data class Grams(val value: Int) : Comparable<Grams> {
        override fun compareTo(other: Grams): Int = value.compareTo(other.value)
    }

    // a type that is BOTH a CharSequence and Comparable, so it fits the where clause
    private class ShelfCode(private val raw: String) : CharSequence by raw, Comparable<ShelfCode> {
        override fun compareTo(other: ShelfCode): Int = raw.compareTo(other.raw)
        override fun toString(): String = raw
    }

    @Test
    fun `maxOfAll works for any Comparable type`() {
        assertThat(maxOfAll(listOf(3, 41, 7))).isEqualTo(41)
        assertThat(maxOfAll(listOf("fig", "pear", "kiwi"))).isEqualTo("pear")
        assertThat(maxOfAll(listOf(Grams(180), Grams(240), Grams(150)))).isEqualTo(Grams(240))
        assertThat(maxOfAll(listOf(LocalDate.of(2026, 3, 1), LocalDate.of(2026, 1, 9)))).isEqualTo(LocalDate.of(2026, 3, 1))
    }

    @Test
    fun `maxOfAll of an empty list throws IllegalArgumentException`() {
        assertThatThrownBy { maxOfAll(emptyList<Int>()) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a Window contains its ends and what is between them`() {
        val frontShelf = Window(Grams(150), Grams(250))
        assertThat(Grams(150) in frontShelf).isTrue()
        assertThat(Grams(250) in frontShelf).isTrue()
        assertThat(Grams(200) in frontShelf).isTrue()
        assertThat(Grams(149) in frontShelf).isFalse()
        assertThat(Grams(251) in frontShelf).isFalse()
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
        assertThat(shortestLabel(listOf("pear", "fig", "kiwi", "mango"))).isEqualTo("fig")
        assertThat(shortestLabel(listOf("yam", "fig", "plum"))).isEqualTo("fig")
        val codes = listOf(ShelfCode("S-0042"), ShelfCode("S-7"), ShelfCode("S-1"))
        assertThat(shortestLabel(codes).toString()).isEqualTo("S-1")
    }

    @Test
    fun `coalesce returns the first non-null value, typed as non-null`() {
        val variety: String = coalesce(null, "Gala", "Fuji")   // String, not String?
        assertThat(variety).isEqualTo("Gala")
        assertThat(coalesce<Int>(null, null, 3)).isEqualTo(3)
    }

    @Test
    fun `coalesce of only nulls throws IllegalArgumentException`() {
        assertThatThrownBy { coalesce<String>(null, null) }.isInstanceOf(IllegalArgumentException::class.java)
    }
}
