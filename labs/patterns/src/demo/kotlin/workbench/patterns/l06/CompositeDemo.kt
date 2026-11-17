package workbench.patterns.l06

// The Saturday breakfast box as a tree. Items and boxes share one sealed type, so one `when` prices them all.

sealed interface ShopGoods {
    data class Item(val name: String, val cents: Long) : ShopGoods
    class Box(contents: List<ShopGoods>) : ShopGoods {
        val contents: List<ShopGoods> = contents.toList()   // copy what we were given: the tree stays immutable
    }
}

private fun price(g: ShopGoods): Long = when (g) {   // no else: a new node type breaks the build
    is ShopGoods.Item -> g.cents
    is ShopGoods.Box -> g.contents.sumOf { price(it) }
}

private fun describe(g: ShopGoods): String = when (g) {
    is ShopGoods.Item -> "${g.name} %d.%02d".format(g.cents / 100, g.cents % 100)
    is ShopGoods.Box -> g.contents.joinToString(" + ", "(", ")") { describe(it) }
}

fun main() {
    val extras = mutableListOf<ShopGoods>(ShopGoods.Item("tea", 450))
    val breakfast = ShopGoods.Box(listOf(ShopGoods.Item("bread", 250), ShopGoods.Item("jam", 300), ShopGoods.Box(extras)))
    println("box: ${describe(breakfast)}")
    println("price: ${price(breakfast)} cents")
    println("a box of two breakfast boxes: ${price(ShopGoods.Box(listOf(breakfast, breakfast)))} cents")

    extras += ShopGoods.Item("champagne", 3_000)          // someone edits the list they passed in
    println("after editing the source list: ${describe(breakfast)}")
}
