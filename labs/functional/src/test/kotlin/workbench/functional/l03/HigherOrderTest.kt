package workbench.functional.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class HigherOrderTest {
    private val addOne: (Long) -> Long = { it + 1 }
    private val double: (Long) -> Long = { it * 2 }

    @Test
    fun `andThen runs the left function first, then the right one`() {
        assertThat((addOne andThen double)(5)).isEqualTo(12)
        assertThat((double andThen addOne)(5)).isEqualTo(11)
    }

    @Test
    fun `andThen can change the type at each step`() {
        val length: (String) -> Int = { it.length }
        val label: (Int) -> String = { "$it chars" }
        assertThat((length andThen label)("pay_123")).isEqualTo("7 chars")
    }

    @Test
    fun `compose runs the right function first`() {
        assertThat((addOne compose double)(5)).isEqualTo(11)
        assertThat((double compose addOne)(5)).isEqualTo(12)
    }

    @Test
    fun `pipeline applies the steps in list order, and an empty pipeline changes nothing`() {
        assertThat(pipeline(listOf(addFlat(25), capAt(100)))(90)).isEqualTo(100)
        assertThat(pipeline(listOf(capAt(100), addFlat(25)))(90)).isEqualTo(115)
        assertThat(pipeline(emptyList<Adjust>())(1_234)).isEqualTo(1_234)
    }

    @Test
    fun `feeFor builds the base fee for a country`() {
        val nl = feeFor("NL")
        assertThat(nl(100_000)).isEqualTo(1_400)
        assertThat(nl(10_000)).isEqualTo(140)
        assertThat(feeFor("US")(10_000)).isEqualTo(290)
    }

    @Test
    fun `feeFor fails for an unknown country when the function is built, not when it is called`() {
        assertThatThrownBy { feeFor("XX") }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("no rate for XX")
    }

    @Test
    fun `merchantFee applies the base fee and then every adjustment in order`() {
        val fee = merchantFee("NL", listOf(discountPercent(10), floorAt(50), capAt(1_000)))
        assertThat(fee(100_000)).isEqualTo(1_000)   // 1,400 -> 1,260 -> 1,260 -> capped at 1,000
        assertThat(fee(2_000)).isEqualTo(50)        // 28 -> 25 -> floored at 50
        assertThat(fee(50_000)).isEqualTo(630)      // 700 -> 630
        assertThat(merchantFee("DE", emptyList())(10_000)).isEqualTo(150)
    }

    @Test
    fun `curried turns a two-argument function into one-argument steps`() {
        val fee: (String, Long) -> Long = { country, amount -> feeFor(country)(amount) }
        val byCountry: (String) -> (Long) -> Long = fee.curried()
        val germany: (Long) -> Long = byCountry("DE")
        assertThat(germany(10_000)).isEqualTo(150)
        assertThat(byCountry("FR")(10_000)).isEqualTo(160)
    }

    @Test
    fun `memoize calls the function once per distinct argument`() {
        var calls = 0
        val slowRate: (String) -> Long = { country -> calls++; BASIS_POINTS.getValue(country) }
        val rate = memoize(slowRate)
        assertThat(listOf(rate("NL"), rate("NL"), rate("DE"), rate("NL"), rate("DE"))).containsExactly(140L, 140L, 150L, 140L, 150L)
        assertThat(calls).`as`("one call for NL and one for DE").isEqualTo(2)
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
