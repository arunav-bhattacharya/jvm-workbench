package workbench.kotlin.l04.demo

data class Item(val sku: String, val qty: Int, val unitMinor: Long)

fun main() {
    val items = buildList {
        add(Item("sku-1", 2, 999))
        add(Item("sku-2", 1, 500))
        if (size == 2) add(Item("gift-wrap", 1, 0))     // `this` is a MutableList, so size works here
    }
    val totals = buildMap {
        for (i in items) put(i.sku, i.qty * i.unitMinor)
    }
    val text = buildString {
        append("total=")
        append(totals.values.sum())
    }
    println(items.map { it.sku })
    println(totals)
    println(text)

    try {
        @Suppress("UNCHECKED_CAST")
        (items as MutableList<Item>).add(Item("late", 1, 1))
    } catch (e: UnsupportedOperationException) {
        println("the built list is read-only: ${e.javaClass.simpleName}")
    }
}
