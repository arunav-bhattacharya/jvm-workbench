package workbench.patterns.l10

/**
 * One shelf in the corner shop: what stands on it, left to right, and the sign on top.
 * Its slots live in a mutable list on purpose.
 */
class ShelfLayout(val name: String) {
    data class Slot(val item: String, val units: Int)

    /** What [save] hands out: a photo of the shelf. Callers can keep it and give it back to [restore], but can't look inside. */
    interface Memento

    private val slots = mutableListOf<Slot>()
    var sign: String = ""

    fun add(slot: Slot) {
        slots += slot
    }

    fun slots(): List<Slot> = slots.toList()

    val totalUnits: Int get() = slots.sumOf { it.units }

    /** A snapshot of the slots and the sign. Later changes to this shelf must not change it. */
    fun save(): Memento = TODO("a private data class that implements Memento and holds COPIES")

    /**
     * Puts the shelf back exactly as it was when [m] was saved. The same memento can be restored more than
     * once. A memento that didn't come from [save] throws IllegalArgumentException.
     */
    fun restore(m: Memento) {
        TODO("check the type with require, then copy the saved slots back in")
    }
}

/** Undo history for one shelf. Keeps at most [limit] checkpoints; the oldest are dropped first. */
class ShelfHistory(private val shelf: ShelfLayout, private val limit: Int) {

    /** Remembers the shelf as it is now. Call it before each change. */
    fun checkpoint() {
        TODO("save a memento; drop the oldest if there are more than limit")
    }

    /** Puts the shelf back to the most recent checkpoint and forgets that checkpoint. False if there is none. */
    fun undo(): Boolean = TODO("restore the newest memento")

    /** How many checkpoints are kept right now. */
    val size: Int
        get() = TODO("the number of kept mementos")
}
