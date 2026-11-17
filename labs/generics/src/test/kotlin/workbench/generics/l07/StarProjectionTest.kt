package workbench.generics.l07

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures
import java.math.BigDecimal

class StarProjectionTest {

    @Test
    fun `describe tells null, text, lists, maps and numbers apart`() {
        assertThat(describe(null)).isEqualTo("nothing")
        assertThat(describe("Gala")).isEqualTo("text Gala")
        assertThat(describe(listOf(180, 150, 120))).isEqualTo("list of 3")
        assertThat(describe(mutableListOf<String>())).isEqualTo("list of 0")
        assertThat(describe(mapOf("Gala" to 180, "Fuji" to 150))).isEqualTo("map of 2")
        assertThat(describe(180)).isEqualTo("number 180")
        assertThat(describe(BigDecimal("2.40"))).isEqualTo("number 2.40")
        assertThat(describe(setOf("a"))).isEqualTo("other")
        assertThat(describe('x')).isEqualTo("other")
    }

    @Test
    fun `stringsIn keeps only the String elements of a list, in order`() {
        assertThat(stringsIn(listOf("Gala", 180, null, "Fuji"))).containsExactly("Gala", "Fuji")
        assertThat(stringsIn(listOf(1, 2))).isEmpty()
    }

    @Test
    fun `stringsIn of something that is not a list is empty`() {
        assertThat(stringsIn("Gala")).isEmpty()
        assertThat(stringsIn(mapOf("Gala" to "x"))).isEmpty()
        assertThat(stringsIn(null)).isEmpty()
    }

    @Test
    fun `render sorts entries by key and wraps them in braces`() {
        assertThat(render(mapOf("lemon" to 120, "apple" to 180))).isEqualTo("{apple=180, lemon=120}")
        assertThat(render(emptyMap<String, Int>())).isEqualTo("{}")
        assertThat(render(mapOf("note" to null))).isEqualTo("{note=null}")
        assertThat(render(mapOf(2 to "b", 1 to "a"))).isEqualTo("{1=a, 2=b}")
    }

    @Test
    fun `render prints a nested map the same way`() {
        val note = mapOf("crates" to 4, "apple" to mapOf("name" to "Gala", "grams" to 180))
        assertThat(render(note)).isEqualTo("{apple={grams=180, name=Gala}, crates=4}")
    }

    @Test
    fun `drain empties the crate and returns how many it removed`() {
        // this call compiles against both MutableList<Any?> and the right type
        val crate = mutableListOf<Any?>("Gala", 2, null)
        assertThat(drain(crate)).isEqualTo(3)
        assertThat(crate).isEmpty()
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
        assertThat(Nulls.countNulls(listOf("Gala", null, "Fuji", null))).isEqualTo(2)
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
