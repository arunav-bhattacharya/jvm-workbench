package workbench.patterns.l09

// A complaint passes along the shop's desk: each handler answers it or passes it on. The order of the list is behavior.

data class Complaint(val orderNo: String, val about: String, val worthCents: Int, val hasReceipt: Boolean)
data class Reply(val from: String, val says: String)

fun interface Handler {
    fun handle(c: Complaint, next: (Complaint) -> Reply): Reply
}

// fold the handlers into one function, from the last to the first
fun desk(handlers: List<Handler>, lastStop: (Complaint) -> Reply): (Complaint) -> Reply =
    handlers.foldRight(lastStop) { h, next -> { c -> h.handle(c, next) } }

fun main() {
    var sorted = 0
    fun sort(who: String): Reply { sorted++; return Reply(who, "sorted") }
    val handled = mutableSetOf<String>()

    val book = Handler { c, next ->
        next(c).also { println("  book: ${c.orderNo} ${c.about} -> ${it.from}") }   // in: nothing; out: write it in the book
    }
    val receipt = Handler { c, next ->
        if (c.hasReceipt) next(c) else Reply("assistant", "please bring the receipt")   // answer now: the rest never runs
    }
    val oncePerOrder = Handler { c, next ->
        if (handled.add(c.orderNo)) next(c) else Reply("assistant", "we sorted this one already")
    }
    val assistant = Handler { c, next -> if (c.worthCents <= 500) sort("assistant") else next(c) }
    val manager = Handler { c, next -> if (c.worthCents <= 5_000) sort("manager") else next(c) }
    val headOffice = { _: Complaint -> sort("head office") }                        // the last stop answers everything

    val shopDesk = desk(listOf(book, receipt, oncePerOrder, assistant, manager), headOffice)

    for (c in listOf(
        Complaint("7781", "cracked teapot", 1_800, true),
        Complaint("7781", "cracked teapot", 1_800, true),     // the same complaint again
        Complaint("7782", "stale bread", 250, false),         // receipt left at home
        Complaint("7782", "stale bread", 250, true),          // back with the receipt
    )) {
        val r = shopDesk(c)
        println("${r.from}: ${r.says}")
    }
    println("complaints sorted: $sorted")
}
