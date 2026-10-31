package workbench.generics.l04

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.generics.JavaSignatures

class CovarianceTest {
    private val c1 = CardPayment("pay_1", 1_200, "4242")
    private val c2 = CardPayment("pay_2", 350, "0005")
    private val t1 = BankTransfer("pay_3", 99_000, "DE89370400440532013000")

    @Test
    fun `Feed hands out items in order and remembers the last one`() {
        val feed = Feed(listOf<Payment>(c1, c2))
        assertThat(feed.lastServed).isNull()
        assertThat(feed.hasNext()).isTrue()
        assertThat(feed.next()).isEqualTo(c1)
        assertThat(feed.lastServed).isEqualTo(c1)
        assertThat(feed.next()).isEqualTo(c2)
        assertThat(feed.lastServed).isEqualTo(c2)
        assertThat(feed.hasNext()).isFalse()
    }

    @Test
    fun `next on an empty feed throws NoSuchElementException`() {
        val feed = Feed(emptyList<Payment>())
        assertThatThrownBy { feed.next() }.isInstanceOf(NoSuchElementException::class.java)
    }

    @Test
    fun `nextOr gives the next item, then the fallback`() {
        val feed = Feed(listOf("EUR"))
        assertThat(feed.nextOr("none")).isEqualTo("EUR")
        assertThat(feed.nextOr("none")).isEqualTo("none")
    }

    @Test
    fun `drainAll and totalCents empty the feed`() {
        assertThat(drainAll(Feed(listOf<Payment>(c1, t1)))).containsExactly(c1, t1)
        val feed = Feed(listOf<Payment>(c1, c2, t1))
        assertThat(totalCents(feed)).isEqualTo(100_550)
        assertThat(feed.hasNext()).isFalse()
    }

    @Test
    fun `Feed is declared out, so Java sees drainAll taking Feed of extends Payment`() {
        // Kotlin writes a ? extends wildcard into a parameter only when the class is declared `out`
        assertThat(JavaSignatures.paramText("workbench.generics.l04.FeedKt", "drainAll"))
            .`as`("drainAll's parameter as Java sees it (add `out` to Feed's type parameter)")
            .isEqualTo("Feed<? extends Payment>")
    }

    @Test
    fun `callers cannot set lastServed`() {
        val publicSetters = Feed::class.java.methods.filter { it.name == "setLastServed" }
        assertThat(publicSetters).isEmpty()
    }

    @Test
    fun `Page map transforms every item and keeps the cursor`() {
        val page = Page(listOf(c1, c2), nextCursor = "cur_77")
        val ids: Page<String> = page.map { it.id }
        assertThat(ids).isEqualTo(Page(listOf("pay_1", "pay_2"), "cur_77"))
    }

    @Test
    fun `firstOnPage returns the first payment or null`() {
        assertThat(firstOnPage(Page(listOf<Payment>(t1, c1), null))).isEqualTo(t1)
        assertThat(firstOnPage(Page(emptyList(), null))).isNull()
    }

    @Test
    fun `Page is declared out, so Java sees firstOnPage taking Page of extends Payment`() {
        assertThat(JavaSignatures.paramText("workbench.generics.l04.PageKt", "firstOnPage"))
            .`as`("firstOnPage's parameter as Java sees it (add `out` to Page's type parameter)")
            .isEqualTo("Page<? extends Payment>")
    }
}
