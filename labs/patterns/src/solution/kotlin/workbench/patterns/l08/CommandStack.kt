package workbench.patterns.l08

class Shelf(val item: String) {
    var units: Int = 0
}

sealed interface ShelfCommand {
    fun apply(shelf: Shelf)
    fun undo(shelf: Shelf)

    data class Restock(val units: Int) : ShelfCommand {
        override fun apply(shelf: Shelf) {
            shelf.units += units
        }

        override fun undo(shelf: Shelf) {
            shelf.units -= units
        }
    }

    data class Sell(val units: Int) : ShelfCommand {
        override fun apply(shelf: Shelf) {
            check(shelf.units >= units) { "not enough on the shelf" }   // throws before changing anything
            shelf.units -= units
        }

        override fun undo(shelf: Shelf) {
            shelf.units += units
        }
    }
}

class CommandStack(private val shelf: Shelf) {
    private val done = ArrayDeque<ShelfCommand>()      // most recent first
    private val undone = ArrayDeque<ShelfCommand>()    // most recently undone first

    val undoable: List<ShelfCommand>
        get() = done.toList()

    fun run(cmd: ShelfCommand) {
        cmd.apply(shelf)            // 1. apply first: if it throws, nothing below runs
        done.addFirst(cmd)          // 2. record only after success
        undone.clear()              // 3. a new action ends the redo history
    }

    fun undo(): Boolean {
        val cmd = done.removeFirstOrNull() ?: return false
        cmd.undo(shelf)
        undone.addFirst(cmd)
        return true
    }

    fun redo(): Boolean {
        val cmd = undone.removeFirstOrNull() ?: return false
        cmd.apply(shelf)
        done.addFirst(cmd)
        return true
    }
}
