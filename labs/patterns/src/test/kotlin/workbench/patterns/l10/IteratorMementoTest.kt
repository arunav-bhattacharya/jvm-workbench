package workbench.patterns.l10

import org.assertj.core.api.Assertions.assertThat
import org.assertj.core.api.Assertions.assertThatThrownBy
import org.junit.jupiter.api.Test
import workbench.patterns.l10.ShelfLayout.Slot

class IteratorMementoTest {

    // ---- iterator ----

    private val pages = mapOf(
        0 to Page(listOf("rye bread", "jam"), 1),
        1 to Page(emptyList(), 2),                   // an empty page in the middle
        2 to Page(listOf("tea"), null),
    )
    private val fetched = mutableListOf<Int>()
    private val fetch: (Int) -> Page = { cursor -> fetched += cursor; pages.getValue(cursor) }

    @Test
    fun `yields every item of every page, skipping an empty page in the middle`() {
        assertThat(pagedSequence(fetch).toList()).containsExactly("rye bread", "jam", "tea")
        assertThat(fetched).containsExactly(0, 1, 2)
    }

    @Test
    fun `fetches nothing until someone iterates, then only the pages it needs`() {
        val stock = pagedSequence(fetch)
        assertThat(fetched).`as`("before iterating").isEmpty()
        assertThat(stock.take(2).toList()).containsExactly("rye bread", "jam")
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
        val stock = pagedSequence(fetch)
        stock.first()
        stock.first()
        assertThat(fetched).containsExactly(0, 0)
    }

    // ---- memento ----

    private fun shelf() = ShelfLayout("breakfast").apply {
        add(Slot("rye bread", 12))
        sign = "Fresh today"
    }

    @Test
    fun `restore puts the slots and the sign back, and later changes don't leak into the snapshot`() {
        val s = shelf()
        val saved = s.save()
        s.add(Slot("jam", 6))
        s.sign = "Autumn sale"
        s.restore(saved)
        assertThat(s.slots()).containsExactly(Slot("rye bread", 12))
        assertThat(s.sign).isEqualTo("Fresh today")
        assertThat(s.totalUnits).isEqualTo(12)
    }

    @Test
    fun `the same memento can be restored twice`() {
        val s = shelf()
        val saved = s.save()
        s.add(Slot("jam", 6))
        s.restore(saved)
        s.add(Slot("tea", 4))
        s.restore(saved)
        assertThat(s.slots()).containsExactly(Slot("rye bread", 12))
    }

    @Test
    fun `a memento that did not come from save is rejected`() {
        val foreign = object : ShelfLayout.Memento {}
        assertThatThrownBy { shelf().restore(foreign) }.isInstanceOf(IllegalArgumentException::class.java)
    }

    @Test
    fun `history undoes changes newest first and says when it is empty`() {
        val s = ShelfLayout("window")
        val history = ShelfHistory(s, limit = 10)
        history.checkpoint()
        s.add(Slot("teapot", 1))
        history.checkpoint()
        s.add(Slot("kettle", 2))
        assertThat(history.undo()).isTrue()
        assertThat(s.slots()).containsExactly(Slot("teapot", 1))
        assertThat(history.undo()).isTrue()
        assertThat(s.slots()).isEmpty()
        assertThat(history.undo()).isFalse()
    }

    @Test
    fun `history keeps only the newest checkpoints`() {
        val s = ShelfLayout("tins")
        val history = ShelfHistory(s, limit = 2)
        for (i in 1..5) {
            history.checkpoint()
            s.add(Slot("tin-$i", i))
        }
        assertThat(history.size).isEqualTo(2)
        assertThat(history.undo()).isTrue()
        assertThat(s.slots().map { it.item }).containsExactly("tin-1", "tin-2", "tin-3", "tin-4")
        assertThat(history.undo()).isTrue()
        assertThat(s.slots().map { it.item }).containsExactly("tin-1", "tin-2", "tin-3")
        assertThat(history.undo()).isFalse()
    }
}
