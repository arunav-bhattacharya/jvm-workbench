package workbench.functional.l01

import org.assertj.core.api.Assertions.assertThat
import org.junit.jupiter.api.AfterEach
import org.junit.jupiter.api.BeforeEach
import org.junit.jupiter.api.Test
import java.time.Clock
import java.time.Instant
import java.time.LocalDate
import java.time.ZoneOffset

class PureShoppingTest {
    private val bag = THE_FLOUR_BAG                      // 1 kg bags, 700 g left, best before 2026-03-31
    private val march2 = LocalDate.of(2026, 3, 2)

    // The shell tests touch two globals, so every test has to reset them. The core tests don't need this.
    @BeforeEach
    @AfterEach
    fun resetGlobals() {
        Cupboard.flour = THE_FLOUR_BAG
        ShoppingList.lines.clear()
    }

    // ---- the functional core: plain values in, a value out, no clock anywhere ----

    @Test
    fun `gramsToBuy rounds what is missing up to whole bags`() {
        assertThat(gramsToBuy(1_500, bag, march2)).isEqualTo(1_000)   // 800 missing: one bag
        assertThat(gramsToBuy(2_500, bag, march2)).isEqualTo(2_000)   // 1,800 missing: two bags
        // exactly 1,000 missing: one bag, not two
        assertThat(gramsToBuy(1_700, bag, march2)).isEqualTo(1_000)
    }

    @Test
    fun `gramsToBuy buys nothing when the cupboard has enough`() {
        assertThat(gramsToBuy(500, bag, march2)).isEqualTo(0)
        assertThat(gramsToBuy(700, bag, march2)).isEqualTo(0)
    }

    @Test
    fun `gramsToBuy counts the bag up to and including its best-before date, not after`() {
        assertThat(gramsToBuy(1_500, bag, LocalDate.of(2026, 3, 31))).isEqualTo(1_000)
        assertThat(gramsToBuy(1_500, bag, LocalDate.of(2026, 4, 1))).isEqualTo(2_000)
        assertThat(gramsToBuy(100, bag, LocalDate.of(2026, 4, 1))).isEqualTo(1_000)
    }

    @Test
    fun `gramsToBuy reads nothing but its arguments`() {
        Cupboard.flour = bag.copy(leftGrams = 50_000)                   // an absurd global: fifty kilos
        val sugar = Bag(sizeGrams = 500, leftGrams = 100, bestBefore = LocalDate.of(2027, 1, 1))
        assertThat(gramsToBuy(1_500, bag, march2))
            .`as`("gramsToBuy must use the bag it is given, not Cupboard")
            .isEqualTo(1_000)
        assertThat(gramsToBuy(1_200, sugar, march2)).isEqualTo(1_500)  // 1,100 missing: three 500 g bags
    }

    @Test
    fun `gramsToBuy changes nothing, gives the same answer every call and writes no shopping lines`() {
        val calls = List(3) { gramsToBuy(1_500, bag, LocalDate.of(2026, 4, 2)) }
        assertThat(calls).containsOnly(2_000)
        assertThat(ShoppingList.lines).`as`("the core must not write the shopping list; the shell does").isEmpty()
    }

    @Test
    fun `shoppingLine builds the text the shell will write`() {
        assertThat(shoppingLine("flour", 1_000, march2)).isEqualTo("2026-03-02: buy 1000 g flour")
    }

    // ---- the imperative shell: these already pass on the original code and must keep passing ----

    private fun clockOn(date: String): Clock = Clock.fixed(Instant.parse("${date}T10:00:00Z"), ZoneOffset.UTC)

    @Test
    fun `flourToBuy before the best-before date counts the bag and writes one line`() {
        assertThat(flourToBuy(1_500, clockOn("2026-03-02"))).isEqualTo(1_000)
        assertThat(ShoppingList.lines).containsExactly("2026-03-02: buy 1000 g flour")
    }

    @Test
    fun `flourToBuy after the best-before date ignores the bag`() {
        assertThat(flourToBuy(1_500, clockOn("2026-04-01"))).isEqualTo(2_000)
        assertThat(ShoppingList.lines).containsExactly("2026-04-01: buy 2000 g flour")
    }

    @Test
    fun `flourToBuy follows the global cupboard`() {
        Cupboard.flour = THE_FLOUR_BAG.copy(leftGrams = 0)
        assertThat(flourToBuy(1_500, clockOn("2026-03-02"))).isEqualTo(2_000)
        assertThat(ShoppingList.lines).hasSize(1)
    }
}
