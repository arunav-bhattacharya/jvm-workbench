package workbench.kotlin.l04

/** Marks the receivers of the print-order DSL. Inside an inner block, the outer builders are no longer implicit. */
@DslMarker
@Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE)
annotation class OrderDsl

enum class Paper { PLAIN, CARD }

/** One part of a booklet, such as its cover or the pages of one chapter. */
data class Part(val name: String, val paper: Paper, val pages: Int)

data class Booklet(val title: String, val note: String, val parts: List<Part>)

data class PrintOrder(val id: String, val booklets: List<Booklet>)

/** Builds one folded booklet. */
@OrderDsl
class BookletBuilder(private val title: String) {
    var note: String = ""
    private val parts = mutableListOf<Part>()

    fun cover(pages: Int) = add("cover", Paper.CARD, pages)

    fun pages(name: String, pages: Int) = add(name, Paper.PLAIN, pages)

    private fun add(name: String, paper: Paper, pages: Int) {
        // fail at the line that is wrong, not later in build()
        require(pages > 0) { "pages must be positive, was $pages for $name" }
        parts += Part(name, paper, pages)
    }

    /** The one place that sees the whole booklet, so it checks the rules that span its parts. */
    fun build(): Booklet {
        require(parts.size >= 2) { "booklet $title needs at least two parts" }
        val total = parts.sumOf { it.pages }
        // one sheet folded in half makes four pages
        require(total % 4 == 0) { "booklet $title has $total pages: a folded booklet needs a multiple of 4" }
        return Booklet(title, note, parts.toList())   // copy: the builder can't change it later
    }
}

/** Builds an order: several booklets printed together. */
@OrderDsl
class OrderBuilder(private val id: String) {
    private val booklets = mutableListOf<Booklet>()

    fun booklet(title: String, block: BookletBuilder.() -> Unit) {
        require(booklets.none { it.title == title }) { "duplicate booklet $title in order ${this.id}" }
        booklets += BookletBuilder(title).apply(block).build()
    }

    fun build(): PrintOrder {
        require(booklets.isNotEmpty()) { "order $id has no booklets" }
        return PrintOrder(id, booklets.toList())
    }
}

/** Entry point: runs [block] with a fresh BookletBuilder as `this`, then validates. */
fun printBooklet(title: String, block: BookletBuilder.() -> Unit): Booklet =
    BookletBuilder(title).apply(block).build()

fun printOrder(id: String, block: OrderBuilder.() -> Unit): PrintOrder =
    OrderBuilder(id).apply(block).build()
