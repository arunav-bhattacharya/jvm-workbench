package workbench.generics.l01

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class GenericsFromZeroTest {
    private data class Payment(val id: String, val cents: Long)

    @Test
    fun `pop returns items in the reverse order of push`() {
        val stack = Stack<String>()
        stack.push("auth")
        stack.push("capture")
        stack.push("settle")
        assertThat(stack.pop()).isEqualTo("settle")
        assertThat(stack.pop()).isEqualTo("capture")
        assertThat(stack.pop()).isEqualTo("auth")
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
        val stack = Stack<Payment>()
        assertThat(stack.peek()).isNull()
        stack.push(Payment("pay_1", 1200))
        val top: Payment? = stack.peek()          // typed as Payment?, no cast needed
        assertThat(top).isEqualTo(Payment("pay_1", 1200))
        assertThat(stack.size).isEqualTo(1)
    }

    @Test
    fun `pop on an empty stack throws NoSuchElementException`() {
        val stack = Stack<String>()
        assertThatThrownBy { stack.pop() }.isInstanceOf(NoSuchElementException::class.java)
    }

    @Test
    fun `firstMatching returns the first match, or null when nothing matches`() {
        val payments = listOf(Payment("a", 500), Payment("b", 25_000), Payment("c", 90_000))
        val big: Payment? = firstMatching(payments) { it.cents > 10_000 }
        assertThat(big?.id).isEqualTo("b")
        assertThat(firstMatching(payments) { it.cents < 0 }).isNull()
        assertThat(firstMatching(listOf("EUR", "USD", "GBP")) { it.startsWith("U") }).isEqualTo("USD")
    }

    @Test
    fun `indexBy keeps the first item for each key`() {
        val payments = listOf(Payment("k1", 100), Payment("k2", 200), Payment("k1", 999))
        val byId: Map<String, Payment> = indexBy(payments) { it.id }
        assertThat(byId).hasSize(2)
        assertThat(byId["k1"]).isEqualTo(Payment("k1", 100))
        val byLength: Map<Int, String> = indexBy(listOf("EUR", "USDT", "GBP")) { it.length }
        assertThat(byLength).containsExactlyEntriesOf(mapOf(3 to "EUR", 4 to "USDT"))
    }

    @Test
    fun `swap flips the values and the types`() {
        val duo: Duo<String, Long> = Duo("pay_7", 4_200L)
        val swapped: Duo<Long, String> = duo.swap()
        assertThat(swapped).isEqualTo(Duo(4_200L, "pay_7"))
    }

    @Test
    fun `mapSecond changes only the second value, and its type`() {
        val duo = Duo("pay_7", 4_200L)
        val shown: Duo<String, String> = duo.mapSecond { cents -> "%.2f EUR".format(java.util.Locale.ROOT, cents / 100.0) }
        assertThat(shown).isEqualTo(Duo("pay_7", "42.00 EUR"))
    }

    @Test
    fun `zipToDuos pairs items by position and stops at the shorter list`() {
        val zipped: List<Duo<Int, String>> = zipToDuos(listOf(1, 2, 3), listOf("a", "b"))
        assertThat(zipped).containsExactly(Duo(1, "a"), Duo(2, "b"))
        assertThat(zipToDuos(emptyList<Int>(), listOf("x"))).isEmpty()
    }
}
