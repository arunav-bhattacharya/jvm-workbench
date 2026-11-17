package workbench.generics.l10

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import java.math.BigDecimal

class AdvancedTest {

    @Test
    fun `a gift box chain keeps the subclass type through the base setters`() {
        val box = GiftBoxBuilder()
            .grams(1_200)           // returns GiftBoxBuilder, not the base class
            .variety("Gala")
            .ribbon("red")          // so this subclass method is still reachable
            .note("for Ana")
            .build()
        assertThat(box).isEqualTo(GiftBox(1_200, "Gala", "for Ana", "red"))
    }

    @Test
    fun `a delivery uses the same base setters and its own address`() {
        val delivery = DeliveryBuilder().address("12 Hill Road").variety("Fuji").grams(2_500).build()
        assertThat(delivery).isEqualTo(Delivery(2_500, "Fuji", "", "12 Hill Road"))
    }

    @Test
    fun `build checks the common fields first`() {
        assertThatThrownBy { GiftBoxBuilder().variety("Gala").ribbon("red").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("weight must be positive")
        assertThatThrownBy { DeliveryBuilder().grams(500).address("12 Hill Road").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("variety is required")
    }

    @Test
    fun `build checks the subclass fields`() {
        assertThatThrownBy { GiftBoxBuilder().grams(500).variety("Gala").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("ribbon is required")
        assertThatThrownBy { DeliveryBuilder().grams(500).variety("Gala").build() }
            .isInstanceOf(IllegalStateException::class.java).hasMessage("address is required")
    }

    @Test
    fun `andThen composes, and accepts a more general second function`() {
        val toGrams: (String) -> Long = { BigDecimal(it).movePointRight(3).longValueExact() }   // kilograms to grams
        val describe: (Any) -> String = { "<$it>" }              // takes Any, not just Long
        val f: (String) -> CharSequence = andThen(toGrams, describe)   // and the result is used as CharSequence
        assertThat(f("1.25").toString()).isEqualTo("<1250>")
    }

    @Test
    fun `andThen runs first before second, once each`() {
        val calls = mutableListOf<String>()
        val f = andThen<Int, Int, Int>({ calls += "first"; it + 1 }, { calls += "second"; it * 10 })
        assertThat(f(4)).isEqualTo(50)
        assertThat(calls).containsExactly("first", "second")
    }

    @Test
    fun `fanOut calls every listener in order, including listeners for a supertype`() {
        val log = mutableListOf<String>()
        val stockCount: Listener<Fruit> = { log += "stock ${it.name}" }
        val signWriter: Listener<Apple> = { log += "sign ${it.grams} g" }
        val all: Listener<Apple> = fanOut(listOf(stockCount, signWriter))   // a Listener<Fruit> fits: in P
        all(Apple("Gala", 180))
        assertThat(log).containsExactly("stock Gala", "sign 180 g")
    }

    @Test
    fun `firstNotNullValue skips nulls and returns a non-null type`() {
        val variety: String = listOf(null, "Gala", "Fuji").firstNotNullValue()   // T = String?, result String
        assertThat(variety).isEqualTo("Gala")
        assertThatThrownBy { listOf<String?>(null, null).firstNotNullValue() }
            .isInstanceOf(NoSuchElementException::class.java).hasMessage("no non-null element")
        assertThatThrownBy { emptyList<Int>().firstNotNullValue() }
            .isInstanceOf(NoSuchElementException::class.java)
    }
}
