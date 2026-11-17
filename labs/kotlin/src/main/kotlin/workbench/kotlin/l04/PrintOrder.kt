package workbench.kotlin.l04

/** Marks the receivers of the print-order DSL. Finished: TODO 5 puts it to use. */
@DslMarker
@Target(AnnotationTarget.CLASS, AnnotationTarget.TYPE)
annotation class OrderDsl

enum class Paper { PLAIN, CARD }

/** One part of a booklet, such as its cover or the pages of one chapter. */
data class Part(val name: String, val paper: Paper, val pages: Int)

data class Booklet(val title: String, val note: String, val parts: List<Part>)

data class PrintOrder(val id: String, val booklets: List<Booklet>)

/**
 * Builds one folded booklet:
 *
 *     printBooklet("menu") {
 *         note = "staple on the fold"
 *         cover(4)
 *         pages("starters", 4)
 *         pages("mains", 8)
 *     }
 *
 * TODO 1: keep the parts in a private list, in the order they were added. cover(pages) adds a part
 * named "cover" on CARD paper; pages(name, pages) adds a part on PLAIN paper. Both reject a page
 * count <= 0 with IllegalArgumentException, right away.
 * TODO 2: build() throws IllegalArgumentException if there are fewer than two parts, or if the pages
 * don't add up to a multiple of 4 (one sheet folded in half makes four pages). The message for the
 * second case is "booklet <title> has <total> pages: a folded booklet needs a multiple of 4".
 * It returns a booklet with a copy of the parts.
 */
class BookletBuilder(private val title: String) {
    var note: String = ""

    fun cover(pages: Int): Unit = TODO("add a part named cover, on CARD paper")

    fun pages(name: String, pages: Int): Unit = TODO("add a part on PLAIN paper")

    fun build(): Booklet = TODO("validate, then Booklet(title, note, copy of parts)")
}

/**
 * Builds an order: several booklets printed together.
 *
 * TODO 3: booklet(title) { ... } builds one booklet with a fresh BookletBuilder and keeps it. A second
 * booklet with the same title throws IllegalArgumentException. build() throws IllegalArgumentException
 * when there are no booklets.
 */
class OrderBuilder(private val id: String) {
    fun booklet(title: String, block: BookletBuilder.() -> Unit): Unit = TODO("BookletBuilder(title).apply(block).build()")

    fun build(): PrintOrder = TODO("PrintOrder(id, copy of booklets)")
}

/** TODO 4: run block with a fresh BookletBuilder as `this`, then build. One line. */
fun printBooklet(title: String, block: BookletBuilder.() -> Unit): Booklet = TODO("BookletBuilder(title).apply(block).build()")

fun printOrder(id: String, block: OrderBuilder.() -> Unit): PrintOrder = TODO("OrderBuilder(id).apply(block).build()")

/*
 * TODO 5: put @OrderDsl on both builder classes (the last test checks it). Before you do, write a
 * scratch function that calls booklet("b2") { ... } inside another booklet { } block of an order.
 * It compiles and quietly adds b2 to the order. Add the marker and read the error you get instead.
 */
