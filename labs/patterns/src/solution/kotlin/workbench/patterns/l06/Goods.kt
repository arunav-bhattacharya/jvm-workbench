package workbench.patterns.l06

sealed interface Goods {
    data class Item(val name: String, val cents: Long) : Goods

    data class ByWeight(val name: String, val grams: Int, val centsPerKg: Long) : Goods

    class Box(contents: List<Goods>) : Goods {
        constructor(vararg contents: Goods) : this(contents.toList())
        val contents: List<Goods> = contents.toList()     // a copy: the box can't change behind your back
    }

    data class PercentOff(val inside: Goods, val percent: Int) : Goods

    data class Deal(val inside: Goods, val maxCents: Long) : Goods
}

// one when, no else: add a sixth node type and this stops compiling until you price it
fun Goods.price(): Long = when (this) {
    is Goods.Item -> cents                                             // leaves compute
    is Goods.ByWeight -> grams * centsPerKg / 1_000
    is Goods.Box -> contents.sumOf { it.price() }                      // groups ask what they hold
    is Goods.PercentOff -> inside.price() * (100 - percent) / 100
    is Goods.Deal -> minOf(inside.price(), maxCents)
}

private fun euros(cents: Long) = "%d.%02d".format(cents / 100, cents % 100)

// a second operation over the same tree: no new classes, just another function
fun Goods.describe(): String = when (this) {
    is Goods.Item -> "$name ${euros(cents)}"
    is Goods.ByWeight -> "$name $grams g"
    is Goods.Box -> contents.joinToString(" + ", "(", ")") { it.describe() }
    is Goods.PercentOff -> "$percent% off ${inside.describe()}"
    is Goods.Deal -> "min(${inside.describe()}, ${euros(maxCents)})"
}
