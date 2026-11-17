package workbench.patterns.l08

/** One shelf in the shop, and how many units of its item are on it. Given; don't change it. */
class Shelf(val item: String) {
    var units: Int = 0
}

/** A request to change a shelf, as a value: it can be stored, logged, queued and undone. */
sealed interface ShelfCommand {
    fun apply(shelf: Shelf)
    fun undo(shelf: Shelf)

    /** Puts [units] more on the shelf. Undo takes them off again. */
    data class Restock(val units: Int) : ShelfCommand {
        override fun apply(shelf: Shelf) {
            TODO("add the units")
        }

        override fun undo(shelf: Shelf) {
            TODO("take them off again")
        }
    }

    /**
     * Takes [units] off the shelf, or throws IllegalStateException("not enough on the shelf")
     * and changes nothing if there are too few. Undo puts them back.
     */
    data class Sell(val units: Int) : ShelfCommand {
        override fun apply(shelf: Shelf) {
            TODO("check the shelf first, then take the units")
        }

        override fun undo(shelf: Shelf) {
            TODO("put them back")
        }
    }
}

/** Runs commands against one shelf and keeps what it needs for undo and redo. */
class CommandStack(private val shelf: Shelf) {

    /** The commands that can be undone, most recent first. */
    val undoable: List<ShelfCommand>
        get() = TODO("a copy of the undo history")

    /**
     * Runs [cmd]. Only a command that succeeded can be undone: one that throws leaves no trace.
     * Running a new command clears the redo history.
     */
    fun run(cmd: ShelfCommand) {
        TODO("apply first, record only after it worked, clear redo")
    }

    /** Undoes the most recent command. Returns false if there is nothing to undo. */
    fun undo(): Boolean = TODO("pop, undo, remember it for redo")

    /** Applies the most recently undone command again. Returns false if there is nothing to redo. */
    fun redo(): Boolean = TODO("pop from redo, apply, push back on the undo history")
}
