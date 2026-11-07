package workbench.patterns.l10

/** A draft invoice an analyst is editing. Its lines live in a mutable list on purpose. */
class InvoiceDraft(val number: String) {
    data class Line(val sku: String, val amountMinor: Long)

    /** What [save] hands out. Callers can keep it and give it back to [restore], but can't look inside. */
    interface Memento

    private val lines = mutableListOf<Line>()
    var note: String = ""

    fun add(line: Line) {
        lines += line
    }

    fun lines(): List<Line> = lines.toList()

    val totalMinor: Long get() = lines.sumOf { it.amountMinor }

    /** A snapshot of the lines and the note. Later edits to this draft must not change it. */
    fun save(): Memento = TODO("a private data class that implements Memento and holds COPIES")

    /**
     * Puts the draft back exactly as it was when [m] was saved. The same memento can be restored more than
     * once. A memento that didn't come from [save] throws IllegalArgumentException.
     */
    fun restore(m: Memento) {
        TODO("check the type with require, then copy the saved lines back in")
    }
}

/** Undo history for one draft. Keeps at most [limit] checkpoints; the oldest are dropped first. */
class DraftHistory(private val draft: InvoiceDraft, private val limit: Int) {

    /** Remembers the draft as it is now. Call it before each edit. */
    fun checkpoint() {
        TODO("save a memento; drop the oldest if there are more than limit")
    }

    /** Puts the draft back to the most recent checkpoint and forgets that checkpoint. False if there is none. */
    fun undo(): Boolean = TODO("restore the newest memento")

    /** How many checkpoints are kept right now. */
    val size: Int
        get() = TODO("the number of kept mementos")
}
