package workbench.patterns.l03

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class OrderDslTest {

    @Test
    fun `the DSL builds an order whose total is the sum of its items`() {
        val o = order {
            customer = "anna@example.com"
            items {
                item("rye bread", 450)
                item("oat milk", 220)
            }
            note("door", "blue gate")
        }
        assertThat(o.customer).isEqualTo("anna@example.com")
        assertThat(o.currency).isEqualTo("EUR")
        assertThat(o.items).containsExactly(Item("rye bread", 450), Item("oat milk", 220))
        assertThat(o.totalCents).isEqualTo(670)
        assertThat(o.notes).containsExactlyEntriesOf(mapOf("door" to "blue gate"))
    }

    @Test
    fun `two items blocks add up, and a repeated note key keeps the last value`() {
        val o = order {
            customer = "ben@example.com"
            currency = "SEK"
            items { item("apples", 100) }
            items { item("pears", 200); item("plums", 300) }
            note("bell", "broken")
            note("bell", "fixed")
        }
        assertThat(o.items.map { it.name }).containsExactly("apples", "pears", "plums")
        assertThat(o.totalCents).isEqualTo(600)
        assertThat(o.currency).isEqualTo("SEK")
        assertThat(o.notes).containsExactlyEntriesOf(mapOf("bell" to "fixed"))
    }

    @Test
    fun `build rejects a missing or blank customer`() {
        assertThatThrownBy { order { items { item("a", 100) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("customer")
        assertThatThrownBy { order { customer = "  "; items { item("a", 100) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("customer")
    }

    @Test
    fun `build rejects a currency that is not three capital letters`() {
        for (bad in listOf("eur", "EURO", "E1R", "")) {
            assertThatThrownBy { order { customer = "c"; currency = bad; items { item("a", 1) } } }
                .`as`("currency '$bad'")
                .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("currency")
        }
    }

    @Test
    fun `build rejects no items, and items with a zero or negative price`() {
        assertThatThrownBy { order { customer = "c" } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("item")
        assertThatThrownBy { order { customer = "c"; items { item("free sample", 0) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("item")
        assertThatThrownBy { order { customer = "c"; items { item("a", 100); item("money back?", -50) } } }
            .isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("item")
    }

    @Test
    fun `a built order does not change when the builder is used again`() {
        val builder = OrderBuilder().apply {
            customer = "cleo@example.com"
            items { item("a", 100) }
            note("floor", "3")
        }
        val first = builder.build()
        builder.items { item("b", 200) }
        builder.note("floor", "4")
        val second = builder.build()
        assertThat(first.items).hasSize(1)
        assertThat(first.notes).containsEntry("floor", "3")
        assertThat(second.items).hasSize(2)
    }

    @Test
    fun `ItemsBuilder hands out a copy of its items`() {
        val b = ItemsBuilder()
        b.item("a", 1)
        val snapshot = b.build()
        b.item("b", 2)
        assertThat(snapshot).hasSize(1)
    }

    @Test
    fun `both builder classes are marked with OrderDsl`() {
        // the compiler enforces the scope rule; this only checks that you put the marker on both builders
        for (cls in listOf(OrderBuilder::class.java, ItemsBuilder::class.java)) {
            assertThat(cls.isAnnotationPresent(OrderDsl::class.java)).`as`("@OrderDsl on ${cls.simpleName}").isTrue()
        }
    }
}
