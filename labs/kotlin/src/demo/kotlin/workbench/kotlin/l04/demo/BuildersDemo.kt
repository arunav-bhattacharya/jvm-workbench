package workbench.kotlin.l04.demo

data class Line(val file: String, val copies: Int, val pages: Int)

fun main() {
    val lines = buildList {
        add(Line("flyer.pdf", 250, 1))
        add(Line("menu.pdf", 40, 8))
        if (size == 2) add(Line("cover-sheet.pdf", 1, 1))   // `this` is a MutableList, so size works here
    }
    val printed = buildMap {
        for (l in lines) put(l.file, l.copies * l.pages)
    }
    val text = buildString {
        append("pages to print=")
        append(printed.values.sum())
    }
    println(lines.map { it.file })
    println(printed)
    println(text)

    try {
        @Suppress("UNCHECKED_CAST")
        (lines as MutableList<Line>).add(Line("late.pdf", 1, 1))
    } catch (e: UnsupportedOperationException) {
        println("the built list is read-only: ${e.javaClass.simpleName}")
    }
}
