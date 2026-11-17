package workbench.patterns.l08

// Commands as data classes, an undo log, and the one rule that keeps undo honest.

class StockShelf { var units = 0 }

sealed interface StockCommand {
    fun apply(s: StockShelf)
    fun undo(s: StockShelf)

    data class Restock(val units: Int) : StockCommand {
        override fun apply(s: StockShelf) { s.units += units }
        override fun undo(s: StockShelf) { s.units -= units }
    }

    data class Sell(val units: Int) : StockCommand {
        override fun apply(s: StockShelf) {
            check(s.units >= units) { "not enough on the shelf" }
            s.units -= units
        }
        override fun undo(s: StockShelf) { s.units += units }
    }
}

class CommandLog {
    val history = ArrayDeque<StockCommand>()

    fun run(c: StockCommand, s: StockShelf) {
        c.apply(s)                   // 1. apply first
        history.addFirst(c)          // 2. record only after it worked
    }

    fun undoLast(s: StockShelf) {
        history.removeFirstOrNull()?.undo(s)
    }
}

fun main() {
    val rye = StockShelf()
    val log = CommandLog()
    log.run(StockCommand.Restock(12), rye)
    log.run(StockCommand.Sell(5), rye)
    try {
        log.run(StockCommand.Sell(40), rye)
    } catch (e: IllegalStateException) {
        println("rejected: ${e.message}")
    }
    println("units ${rye.units}, history ${log.history}")
    log.undoLast(rye)
    println("after one undo: units ${rye.units}, history ${log.history}")
}
