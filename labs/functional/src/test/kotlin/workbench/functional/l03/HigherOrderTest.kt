package workbench.functional.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class HigherOrderTest {
    private val addOne: (Int) -> Int = { it + 1 }
    private val double: (Int) -> Int = { it * 2 }

    @Test
    fun `andThen runs the left function first, then the right one`() {
        assertThat((addOne andThen double)(5)).isEqualTo(12)
        assertThat((double andThen addOne)(5)).isEqualTo(11)
    }

    @Test
    fun `andThen can change the type at each step`() {
        val length: (String) -> Int = { it.length }
        val label: (Int) -> String = { "$it letters" }
        assertThat((length andThen label)("pancakes")).isEqualTo("8 letters")
    }

    @Test
    fun `compose runs the right function first`() {
        assertThat((addOne compose double)(5)).isEqualTo(11)
        assertThat((double compose addOne)(5)).isEqualTo(12)
    }

    @Test
    fun `pipeline applies the steps in list order, and an empty pipeline changes nothing`() {
        assertThat(pipeline(listOf(add(25), atMost(100)))(90)).isEqualTo(100)
        assertThat(pipeline(listOf(atMost(100), add(25)))(90)).isEqualTo(115)
        assertThat(pipeline(emptyList<Step>())(1_234)).isEqualTo(1_234)
    }

    @Test
    fun `gramsFor builds the jug-to-scale function for an ingredient`() {
        val flour = gramsFor("flour")
        assertThat(flour(1_000)).isEqualTo(530)
        assertThat(flour(500)).isEqualTo(265)
        assertThat(gramsFor("honey")(250)).isEqualTo(355)
    }

    @Test
    fun `gramsFor fails for an unknown ingredient when the function is built, not when it is called`() {
        assertThatThrownBy { gramsFor("sand") }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("unknown ingredient sand")
    }

    @Test
    fun `weighOut converts first and then applies every step in order`() {
        val sugar = weighOut("sugar", listOf(percentLess(10), atLeast(50), atMost(300)))
        assertThat(sugar(500)).isEqualTo(300)   // 425 -> 382 -> 382 -> at most 300
        assertThat(sugar(50)).isEqualTo(50)     // 42 -> 37 -> at least 50
        assertThat(sugar(300)).isEqualTo(229)   // 255 -> 229
        assertThat(weighOut("milk", emptyList())(1_000)).isEqualTo(1_030)
    }

    @Test
    fun `curried turns a two-argument function into one-argument steps`() {
        val grams: (String, Int) -> Int = { ingredient, ml -> gramsFor(ingredient)(ml) }
        val byIngredient: (String) -> (Int) -> Int = grams.curried()
        val sugar: (Int) -> Int = byIngredient("sugar")
        assertThat(sugar(1_000)).isEqualTo(850)
        assertThat(byIngredient("honey")(100)).isEqualTo(142)
    }

    @Test
    fun `memoize calls the function once per distinct argument`() {
        var calls = 0
        val slowWeight: (String) -> Int = { ingredient -> calls++; GRAMS_PER_LITRE.getValue(ingredient) }
        val weight = memoize(slowWeight)
        assertThat(listOf(weight("flour"), weight("flour"), weight("honey"), weight("flour"), weight("honey")))
            .containsExactly(530, 530, 1_420, 530, 1_420)
        assertThat(calls).`as`("one call for flour and one for honey").isEqualTo(2)
    }

    @Test
    fun `each memoized function has its own cache`() {
        var calls = 0
        val square: (Long) -> Long = { calls++; it * it }
        val first = memoize(square)
        val second = memoize(square)
        first(12)
        second(12)
        assertThat(calls).isEqualTo(2)
        first(12)
        assertThat(calls).isEqualTo(2)
    }
}
