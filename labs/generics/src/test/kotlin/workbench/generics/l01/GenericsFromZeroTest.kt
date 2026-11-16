package workbench.generics.l01

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class GenericsFromZeroTest {
    private data class Apple(val variety: String, val grams: Int)

    @Test
    fun `pop returns items in the reverse order of push`() {
        val stack = Stack<String>()
        stack.push("wash")
        stack.push("sort")
        stack.push("pack")
        assertThat(stack.pop()).isEqualTo("pack")
        assertThat(stack.pop()).isEqualTo("sort")
        assertThat(stack.pop()).isEqualTo("wash")
    }

    @Test
    fun `size and isEmpty follow pushes and pops`() {
        val stack = Stack<Int>()
        assertThat(stack.isEmpty()).isTrue()
        assertThat(stack.size).isZero()
        stack.push(1)
        stack.push(2)
        assertThat(stack.size).isEqualTo(2)
        stack.pop()
        assertThat(stack.size).isEqualTo(1)
        assertThat(stack.isEmpty()).isFalse()
    }

    @Test
    fun `peek shows the top item without removing it, and is null when empty`() {
        val stack = Stack<Apple>()
        assertThat(stack.peek()).isNull()
        stack.push(Apple("Gala", 180))
        val top: Apple? = stack.peek()            // typed as Apple?, no cast needed
        assertThat(top).isEqualTo(Apple("Gala", 180))
        assertThat(stack.size).isEqualTo(1)
    }

    @Test
    fun `pop on an empty stack throws NoSuchElementException`() {
        val stack = Stack<String>()
        assertThatThrownBy { stack.pop() }.isInstanceOf(NoSuchElementException::class.java)
    }

    @Test
    fun `firstMatching returns the first match, or null when nothing matches`() {
        val apples = listOf(Apple("Gala", 150), Apple("Fuji", 210), Apple("Braeburn", 240))
        val big: Apple? = firstMatching(apples) { it.grams > 200 }
        assertThat(big?.variety).isEqualTo("Fuji")
        assertThat(firstMatching(apples) { it.grams < 0 }).isNull()
        assertThat(firstMatching(listOf("fig", "kiwi", "lime")) { it.startsWith("k") }).isEqualTo("kiwi")
    }

    @Test
    fun `indexBy keeps the first item for each key`() {
        val apples = listOf(Apple("Gala", 150), Apple("Fuji", 210), Apple("Gala", 999))
        val byVariety: Map<String, Apple> = indexBy(apples) { it.variety }
        assertThat(byVariety).hasSize(2)
        assertThat(byVariety["Gala"]).isEqualTo(Apple("Gala", 150))
        val byLength: Map<Int, String> = indexBy(listOf("fig", "kiwi", "yam")) { it.length }
        assertThat(byLength).containsExactlyEntriesOf(mapOf(3 to "fig", 4 to "kiwi"))
    }

    @Test
    fun `swap flips the values and the types`() {
        val duo: Duo<String, Int> = Duo("Gala", 180)
        val swapped: Duo<Int, String> = duo.swap()
        assertThat(swapped).isEqualTo(Duo(180, "Gala"))
    }

    @Test
    fun `mapSecond changes only the second value, and its type`() {
        val duo = Duo("Gala", 180)
        val shown: Duo<String, String> = duo.mapSecond { grams -> "%.2f kg".format(java.util.Locale.ROOT, grams / 1000.0) }
        assertThat(shown).isEqualTo(Duo("Gala", "0.18 kg"))
    }

    @Test
    fun `zipToDuos pairs items by position and stops at the shorter list`() {
        val zipped: List<Duo<Int, String>> = zipToDuos(listOf(1, 2, 3), listOf("a", "b"))
        assertThat(zipped).containsExactly(Duo(1, "a"), Duo(2, "b"))
        assertThat(zipToDuos(emptyList<Int>(), listOf("x"))).isEmpty()
    }
}
