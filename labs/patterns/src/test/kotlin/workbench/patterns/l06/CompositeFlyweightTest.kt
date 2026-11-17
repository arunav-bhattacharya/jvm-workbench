package workbench.patterns.l06

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.patterns.l06.Goods.Box
import workbench.patterns.l06.Goods.ByWeight
import workbench.patterns.l06.Goods.Deal
import workbench.patterns.l06.Goods.Item
import workbench.patterns.l06.Goods.PercentOff
import java.util.Collections
import java.util.IdentityHashMap
import java.util.concurrent.CountDownLatch
import kotlin.concurrent.thread

class CompositeFlyweightTest {

    // ---- composite ----

    private val breakfast = Box(Item("bread", 250), Item("jam", 300), Box(Item("tea", 450)))

    @Test
    fun `bread, jam and a small box of tea add up to 10 euros`() {
        assertThat(breakfast.price()).isEqualTo(1_000)
        assertThat(Box(breakfast, breakfast).price()).`as`("a box of two breakfast boxes").isEqualTo(2_000)
    }

    @Test
    fun `leaves price on their own, rounding weights down to the cent`() {
        assertThat(Item("jam", 300).price()).isEqualTo(300)
        assertThat(ByWeight("coffee", 250, 2_400).price()).isEqualTo(600)
        assertThat(ByWeight("pepper", 33, 1_999).price()).`as`("65.967 cents").isEqualTo(65)
        assertThat(Box().price()).`as`("an empty box").isEqualTo(0)
    }

    @Test
    fun `PercentOff takes its percent off what it holds, rounding down`() {
        assertThat(PercentOff(Box(Item("bread", 250), Item("jam", 300)), 10).price()).`as`("10% off 5.50").isEqualTo(495)
        assertThat(PercentOff(Item("cake", 999), 15).price()).`as`("849.15 cents").isEqualTo(849)
    }

    @Test
    fun `a Deal never charges more than its maximum, at any depth`() {
        val bread = Item("bread", 250)
        val jam = Item("jam", 300)
        assertThat(Deal(Box(bread, jam, Item("butter", 400)), 800).price()).isEqualTo(800)
        assertThat(Deal(Box(bread, jam), 800).price()).isEqualTo(550)
        val nested = Box(Item("card", 100), Deal(PercentOff(Item("cake", 1_200), 25), 850))
        assertThat(nested.price()).`as`("1.00 + min(9.00, 8.50)").isEqualTo(950)
    }

    @Test
    fun `describe renders every node type`() {
        assertThat(breakfast.describe()).isEqualTo("(bread 2.50 + jam 3.00 + (tea 4.50))")
        assertThat(Deal(PercentOff(ByWeight("coffee", 250, 2_400), 5), 500).describe())
            .isEqualTo("min(5% off coffee 250 g, 5.00)")
        assertThat(Box().describe()).isEqualTo("()")
        assertThat(Item("card", 5).describe()).isEqualTo("card 0.05")
    }

    // ---- flyweight ----

    @Test
    fun `the same code always gives the same instance`() {
        val a = Product.of("T-1001")
        val b = Product.of("T-1001")
        assertThat(a).isSameAs(b)
        assertThat(a.name).isEqualTo("Breakfast tea")
        assertThat(Product.of("J-2001")).isNotSameAs(a)
    }

    @Test
    fun `an unknown code is rejected and never pooled`() {
        assertThatThrownBy { Product.of("X-0000") }
            .isInstanceOf(IllegalArgumentException::class.java)
            .hasMessage("unknown product: X-0000")
    }

    @Test
    fun `eight threads asking at once share one instance and build it at most once`() {
        val before = Product.instancesCreated
        val seen: MutableSet<Product> = Collections.synchronizedSet(Collections.newSetFromMap(IdentityHashMap()))
        val go = CountDownLatch(1)
        val threads = List(8) {
            thread {
                go.await()
                repeat(2_000) { seen += Product.of("B-3001") }
            }
        }
        go.countDown()
        threads.forEach { it.join() }
        assertThat(seen).`as`("distinct instances handed out").hasSize(1)
        assertThat(Product.instancesCreated - before).`as`("constructor runs").isLessThanOrEqualTo(1)
    }
}
