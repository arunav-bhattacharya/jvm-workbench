package workbench.functional.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.assertj.core.api.Assertions.entry
import org.junit.jupiter.api.Test
import workbench.functional.l04.Status.BURNT
import workbench.functional.l04.Status.GOLDEN
import workbench.functional.l04.Status.RAW

class BakeReportTest {
    private val c1 = Cookie("c1", "oat", 45, GOLDEN)
    private val c2 = Cookie("c2", "chocolate", 90, RAW)
    private val c3 = Cookie("c3", "oat", 50, GOLDEN, nibbledGrams = 10)
    private val c4 = Cookie("c4", "ginger", 80, BURNT)
    private val c5 = Cookie("c5", "chocolate", 30, GOLDEN)
    private val day = listOf(Tray("t1", listOf(c1, c2, c3)), Tray("t2", listOf(c4, c5)))
    private val all = listOf(c1, c2, c3, c4, c5)

    @Test
    fun `allCookies flattens the trays in order`() {
        assertThat(allCookies(day)).containsExactly(c1, c2, c3, c4, c5)
        assertThat(allCookies(listOf(Tray("empty", emptyList())))).isEmpty()
    }

    @Test
    fun `goldenGrams counts only golden cookies, and 0 for none`() {
        assertThat(goldenGrams(all)).isEqualTo(125)
        assertThat(goldenGrams(listOf(c2, c4))).isEqualTo(0)
        assertThat(goldenGrams(emptyList())).isEqualTo(0)
    }

    @Test
    fun `nibbledGrams adds up the bites that were taken`() {
        assertThat(nibbledGrams(all)).isEqualTo(10)
        assertThat(nibbledGrams(listOf(c1, c2))).isEqualTo(0)
    }

    @Test
    fun `netByFlavor subtracts bites and keeps flavors in first-seen order`() {
        assertThat(netByFlavor(all)).containsExactly(entry("oat", 85), entry("chocolate", 30))
        val walnutFirst = listOf(Cookie("w1", "walnut", 30, GOLDEN), Cookie("a1", "almond", 20, GOLDEN), Cookie("w2", "walnut", 25, GOLDEN))
        assertThat(netByFlavor(walnutFirst).keys).`as`("first-seen order, not sorted").containsExactly("walnut", "almond")
        assertThat(netByFlavor(listOf(c2, c4))).isEmpty()
    }

    @Test
    fun `burntIds lists burnt cookies in input order`() {
        val c6 = Cookie("c6", "oat", 40, BURNT)
        assertThat(burntIds(all + c6)).containsExactly("c4", "c6")
        assertThat(burntIds(emptyList())).isEmpty()
    }

    @Test
    fun `largestGolden ignores cookies that aren't golden and is null when none are`() {
        assertThat(largestGolden(all)).`as`("c2 and c4 are heavier, but not golden").isEqualTo(c3)
        assertThat(largestGolden(listOf(c2, c4))).isNull()
        assertThat(largestGolden(emptyList())).isNull()
    }

    @Test
    fun `jarGrams folds every cookie into what the jar already holds`() {
        assertThat(jarGrams(200, all)).isEqualTo(315)   // + 45 + (50 - 10) + 30
        assertThat(jarGrams(200, emptyList())).isEqualTo(200)
        assertThat(jarGrams(0, listOf(c2, c4))).isEqualTo(0)
    }

    @Test
    fun `indexById maps each id to its cookie`() {
        val index = indexById(all)
        assertThat(index).hasSize(5)
        assertThat(index["c3"]).isEqualTo(c3)
        assertThat(indexById(emptyList())).isEmpty()
    }

    @Test
    fun `indexById rejects repeated ids and names each one once, in first-seen order`() {
        val c7 = Cookie("c7", "oat", 44, GOLDEN)
        val countedTwice = listOf(c1, c2, c7, c2.copy(), c7.copy(grams = 43), c2.copy())
        assertThatThrownBy { indexById(countedTwice) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("duplicate cookie ids: c2, c7")
    }

    @Test
    fun `bakeReport matches the loop version on a normal day`() {
        val expected = BakeReport(5, 125, 10, mapOf("oat" to 85, "chocolate" to 30), listOf("c4"), c3)
        assertThat(bakeReport(day)).isEqualTo(expected)
        assertThat(bakeReport(day)).isEqualTo(bakeReportLoop(day))
    }

    @Test
    fun `bakeReport on a day with no cookies gives zeros, not an exception`() {
        val empty = BakeReport(0, 0, 0, emptyMap(), emptyList(), null)
        assertThat(bakeReport(emptyList())).isEqualTo(empty)
        assertThat(bakeReport(listOf(Tray("t1", emptyList())))).isEqualTo(empty)
    }

    @Test
    fun `bakeReport refuses a day where a tray was written down twice`() {
        val countedTwice = listOf(Tray("t1", listOf(c1, c2)), Tray("t1-again", listOf(c2, c3)))
        assertThatThrownBy { bakeReport(countedTwice) }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("duplicate cookie ids: c2")
    }
}
