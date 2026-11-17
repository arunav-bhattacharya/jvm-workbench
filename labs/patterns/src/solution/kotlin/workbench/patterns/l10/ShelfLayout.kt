package workbench.patterns.l10

class ShelfLayout(val name: String) {
    data class Slot(val item: String, val units: Int)

    interface Memento

    // private: only the shelf can read a snapshot, so nobody else depends on its insides
    private data class Photo(val slots: List<Slot>, val sign: String) : Memento

    private val slots = mutableListOf<Slot>()
    var sign: String = ""

    fun add(slot: Slot) {
        slots += slot
    }

    fun slots(): List<Slot> = slots.toList()

    val totalUnits: Int get() = slots.sumOf { it.units }

    // copy the mutable list: storing `slots` itself would let later changes leak into the snapshot
    fun save(): Memento = Photo(slots.toList(), sign)

    fun restore(m: Memento) {
        require(m is Photo) { "not a memento from ShelfLayout.save()" }   // smart-casts m to Photo below
        slots.clear()
        slots.addAll(m.slots)            // copy back in: the memento stays untouched, so it can be restored again
        sign = m.sign
    }
}

class ShelfHistory(private val shelf: ShelfLayout, private val limit: Int) {
    private val photos = ArrayDeque<ShelfLayout.Memento>()

    fun checkpoint() {
        photos.addLast(shelf.save())
        if (photos.size > limit) photos.removeFirst()     // bounded: an unbounded history is a slow leak
    }

    fun undo(): Boolean {
        val m = photos.removeLastOrNull() ?: return false
        shelf.restore(m)
        return true
    }

    val size: Int
        get() = photos.size
}
