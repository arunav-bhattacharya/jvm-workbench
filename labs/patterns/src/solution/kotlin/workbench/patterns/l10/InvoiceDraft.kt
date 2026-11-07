package workbench.patterns.l10

class InvoiceDraft(val number: String) {
    data class Line(val sku: String, val amountMinor: Long)

    interface Memento

    // private: only the draft can read a snapshot, so nobody else depends on its insides
    private data class State(val lines: List<Line>, val note: String) : Memento

    private val lines = mutableListOf<Line>()
    var note: String = ""

    fun add(line: Line) {
        lines += line
    }

    fun lines(): List<Line> = lines.toList()

    val totalMinor: Long get() = lines.sumOf { it.amountMinor }

    // copy the mutable list: storing `lines` itself would let later edits leak into the snapshot
    fun save(): Memento = State(lines.toList(), note)

    fun restore(m: Memento) {
        require(m is State) { "not a memento from InvoiceDraft.save()" }   // smart-casts m to State below
        lines.clear()
        lines.addAll(m.lines)            // copy back in: the memento stays untouched, so it can be restored again
        note = m.note
    }
}

class DraftHistory(private val draft: InvoiceDraft, private val limit: Int) {
    private val snapshots = ArrayDeque<InvoiceDraft.Memento>()

    fun checkpoint() {
        snapshots.addLast(draft.save())
        if (snapshots.size > limit) snapshots.removeFirst()     // bounded: an unbounded history is a slow leak
    }

    fun undo(): Boolean {
        val m = snapshots.removeLastOrNull() ?: return false
        draft.restore(m)
        return true
    }

    val size: Int
        get() = snapshots.size
}
