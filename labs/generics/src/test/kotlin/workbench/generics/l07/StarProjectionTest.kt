package workbench.generics.l07

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures
import java.math.BigDecimal

class StarProjectionTest {

    @Test
    fun `describe tells null, text, lists, maps and numbers apart`() {
        assertThat(describe(null)).isEqualTo("nothing")
        assertThat(describe("EUR")).isEqualTo("text EUR")
        assertThat(describe(listOf(1_200, 350, 99))).isEqualTo("list of 3")
        assertThat(describe(mutableListOf<String>())).isEqualTo("list of 0")
        assertThat(describe(mapOf("EUR" to 1_200, "USD" to 350))).isEqualTo("map of 2")
        assertThat(describe(1_200)).isEqualTo("number 1200")
        assertThat(describe(BigDecimal("12.50"))).isEqualTo("number 12.50")
        assertThat(describe(setOf("a"))).isEqualTo("other")
        assertThat(describe('x')).isEqualTo("other")
    }

    @Test
    fun `stringsIn keeps only the String elements of a list, in order`() {
        assertThat(stringsIn(listOf("EUR", 1_200, null, "USD"))).containsExactly("EUR", "USD")
        assertThat(stringsIn(listOf(1, 2))).isEmpty()
    }

    @Test
    fun `stringsIn of something that is not a list is empty`() {
        assertThat(stringsIn("EUR")).isEmpty()
        assertThat(stringsIn(mapOf("EUR" to "x"))).isEmpty()
        assertThat(stringsIn(null)).isEmpty()
    }

    @Test
    fun `render sorts entries by key and wraps them in braces`() {
        assertThat(render(mapOf("USD" to 350, "EUR" to 1_200))).isEqualTo("{EUR=1200, USD=350}")
        assertThat(render(emptyMap<String, Int>())).isEqualTo("{}")
        assertThat(render(mapOf("note" to null))).isEqualTo("{note=null}")
        assertThat(render(mapOf(2 to "b", 1 to "a"))).isEqualTo("{1=a, 2=b}")
    }

    @Test
    fun `render prints a nested map the same way`() {
        val auth = mapOf("cents" to 99, "card" to mapOf("scheme" to "visa", "last4" to "4242"))
        assertThat(render(auth)).isEqualTo("{card={last4=4242, scheme=visa}, cents=99}")
    }

    @Test
    fun `drain empties the buffer and returns how many it removed`() {
        // this call compiles against both MutableList<Any?> and the right type
        val buffer = mutableListOf<Any?>("pay_1", 2, null)
        assertThat(drain(buffer)).isEqualTo(3)
        assertThat(buffer).isEmpty()
    }

    @Test
    fun `drain takes a mutable list of any element type, which Java sees as List of question mark`() {
        // MutableList<Any?> compiles to List<Object>, which rejects a MutableList<String>.
        // A star projection compiles to List<?>.
        assertThat(JavaSignatures.paramText("workbench.generics.l07.DescribeKt", "drain", 0))
            .`as`("drain's parameter as Java sees it")
            .isEqualTo("List<?>")
    }

    @Test
    fun `countNulls counts the null elements of any list`() {
        assertThat(Nulls.countNulls(listOf("pay_1", null, "pay_2", null))).isEqualTo(2)
        assertThat(Nulls.countNulls(listOf(1, 2))).isZero()
        assertThat(Nulls.countNulls(emptyList<String>())).isZero()
    }

    @Test
    fun `countNulls takes List of question mark, not a raw List`() {
        assertThat(JavaSignatures.paramText("workbench.generics.l07.Nulls", "countNulls", 0))
            .`as`("countNulls's parameter (replace the raw type with a wildcard)")
            .isEqualTo("List<?>")
    }
}
