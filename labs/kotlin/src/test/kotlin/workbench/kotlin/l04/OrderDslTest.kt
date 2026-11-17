package workbench.kotlin.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test

class OrderDslTest {

    private fun menu() = printBooklet("menu") {
        note = "staple on the fold"
        cover(4)
        pages("starters", 4)
        pages("mains", 8)
    }

    @Test
    fun `printBooklet builds a booklet with the parts in order`() {
        val b = menu()
        assertThat(b.title).isEqualTo("menu")
        assertThat(b.note).isEqualTo("staple on the fold")
        assertThat(b.parts).containsExactly(
            Part("cover", Paper.CARD, 4),
            Part("starters", Paper.PLAIN, 4),
            Part("mains", Paper.PLAIN, 8),
        )
    }

    @Test
    fun `a booklet that doesn't fold is rejected with its title and page count in the message`() {
        assertThatThrownBy {
            printBooklet("programme") {
                cover(4)
                pages("concert", 10)
            }
        }.isInstanceOf(IllegalArgumentException::class.java)
            .hasMessageContaining("programme")
            .hasMessageContaining("14")
    }

    @Test
    fun `non-positive page counts and one-part booklets are rejected`() {
        assertThatThrownBy { printBooklet("x") { cover(0); pages("a", 4) } }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { printBooklet("x") { cover(4); pages("a", -4) } }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { printBooklet("x") { cover(4) } }
            .isInstanceOf(IllegalArgumentException::class.java)
        assertThatThrownBy { printBooklet("x") { note = "empty" } }
            .isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `an order collects booklets in order and rejects a duplicate title`() {
        val o = printOrder("ord-17") {
            booklet("menu") { cover(4); pages("dishes", 8) }
            booklet("programme") { cover(4); pages("concert", 12) }
        }
        assertThat(o.booklets.map { it.title }).containsExactly("menu", "programme")

        assertThatThrownBy {
            printOrder("ord-18") {
                booklet("menu") { cover(4); pages("a", 4) }
                booklet("menu") { cover(4); pages("a", 4) }
            }
        }.isInstanceOf(IllegalArgumentException::class.java).hasMessageContaining("menu")

        assertThatThrownBy { printOrder("ord-19") { } }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `a built booklet keeps its own copy of the parts`() {
        val builder = BookletBuilder("b-1")
        builder.cover(4)
        builder.pages("inside", 4)
        val first = builder.build()
        builder.pages("more", 4)                     // the builder carries on...
        builder.pages("even more", 4)
        assertThat(first.parts).hasSize(2)           // ...but the booklet already built must not change
        assertThat(builder.build().parts).hasSize(4)
    }

    @Test
    fun `both builders carry the OrderDsl marker`() {
        for (builder in listOf(BookletBuilder::class.java, OrderBuilder::class.java)) {
            assertThat(builder.isAnnotationPresent(OrderDsl::class.java)).`as`(builder.simpleName).isTrue()
        }
    }
}
