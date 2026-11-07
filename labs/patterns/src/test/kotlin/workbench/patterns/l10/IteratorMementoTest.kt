package workbench.patterns.l10

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.patterns.l10.InvoiceDraft.Line

class IteratorMementoTest {

    // ---- iterator ----

    private val pages = mapOf(
        0 to Page(listOf("rf_1", "rf_2"), 1),
        1 to Page(emptyList(), 2),                   // an empty page in the middle
        2 to Page(listOf("rf_3"), null),
    )
    private val fetched = mutableListOf<Int>()
    private val fetch: (Int) -> Page = { cursor -> fetched += cursor; pages.getValue(cursor) }

    @Test
    fun `yields every item of every page, skipping an empty page in the middle`() {
        assertThat(pagedSequence(fetch).toList()).containsExactly("rf_1", "rf_2", "rf_3")
        assertThat(fetched).containsExactly(0, 1, 2)
    }

    @Test
    fun `fetches nothing until someone iterates, then only the pages it needs`() {
        val refunds = pagedSequence(fetch)
        assertThat(fetched).`as`("before iterating").isEmpty()
        assertThat(refunds.take(2).toList()).containsExactly("rf_1", "rf_2")
        assertThat(fetched).`as`("after take(2)").containsExactly(0)
    }

    @Test
    fun `an empty last page ends the sequence`() {
        val none = pagedSequence { cursor -> fetched += cursor; Page(emptyList(), null) }
        assertThat(none.toList()).isEmpty()
        assertThat(fetched).containsExactly(0)
    }

    @Test
    fun `the sequence is cold, so iterating it again fetches again`() {
        val refunds = pagedSequence(fetch)
        refunds.first()
        refunds.first()
        assertThat(fetched).containsExactly(0, 0)
    }

    // ---- memento ----

    private fun draft() = InvoiceDraft("INV-0042").apply {
        add(Line("sku-1", 1_000))
        note = "first draft"
    }

    @Test
    fun `restore puts the lines and the note back, and later edits don't leak into the snapshot`() {
        val d = draft()
        val saved = d.save()
        d.add(Line("sku-2", 2_500))
        d.note = "edited"
        d.restore(saved)
        assertThat(d.lines()).containsExactly(Line("sku-1", 1_000))
        assertThat(d.note).isEqualTo("first draft")
        assertThat(d.totalMinor).isEqualTo(1_000)
    }

    @Test
    fun `the same memento can be restored twice`() {
        val d = draft()
        val saved = d.save()
        d.add(Line("sku-2", 2_500))
        d.restore(saved)
        d.add(Line("sku-3", 700))
        d.restore(saved)
        assertThat(d.lines()).containsExactly(Line("sku-1", 1_000))
    }

    @Test
    fun `a memento that did not come from save is rejected`() {
        val foreign = object : InvoiceDraft.Memento {}
        assertThatThrownBy { draft().restore(foreign) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `history undoes edits newest first and says when it is empty`() {
        val d = InvoiceDraft("INV-0043")
        val history = DraftHistory(d, limit = 10)
        history.checkpoint()
        d.add(Line("a", 100))
        history.checkpoint()
        d.add(Line("b", 200))
        assertThat(history.undo()).isTrue()
        assertThat(d.lines()).containsExactly(Line("a", 100))
        assertThat(history.undo()).isTrue()
        assertThat(d.lines()).isEmpty()
        assertThat(history.undo()).isFalse()
    }

    @Test
    fun `history keeps only the newest checkpoints`() {
        val d = InvoiceDraft("INV-0044")
        val history = DraftHistory(d, limit = 2)
        for (i in 1..5) {
            history.checkpoint()
            d.add(Line("sku-$i", i * 100L))
        }
        assertThat(history.size).isEqualTo(2)
        assertThat(history.undo()).isTrue()
        assertThat(d.lines().map { it.sku }).containsExactly("sku-1", "sku-2", "sku-3", "sku-4")
        assertThat(history.undo()).isTrue()
        assertThat(d.lines().map { it.sku }).containsExactly("sku-1", "sku-2", "sku-3")
        assertThat(history.undo()).isFalse()
    }
}
