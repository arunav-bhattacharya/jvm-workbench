package workbench.patterns.l06

/**
 * What the corner shop sells, as a tree. [Item] and [ByWeight] are leaves; [Box] holds other goods,
 * and [PercentOff] and [Deal] each wrap one. Every node is [Goods], so code that prices a box never
 * has to ask "is this one thing or a group?".
 *
 * Prices are in cents: 250 means 2.50. Use integer division (it rounds down).
 */
sealed interface Goods {
    /** One thing at a fixed price, such as a jar of jam. */
    data class Item(val name: String, val cents: Long) : Goods

    /** Sold by weight: [grams] of it at [centsPerKg]. */
    data class ByWeight(val name: String, val grams: Int, val centsPerKg: Long) : Goods

    /** A box of goods: its price is the sum of what is inside. An empty box costs 0. */
    data class Box(val contents: List<Goods>) : Goods {
        constructor(vararg contents: Goods) : this(contents.toList())
    }

    /** [percent] off whatever [inside] costs, rounded down: 10% off 5.50 is 4.95. */
    data class PercentOff(val inside: Goods, val percent: Int) : Goods

    /** A deal: whatever [inside] costs, but never more than [maxCents]. */
    data class Deal(val inside: Goods, val maxCents: Long) : Goods
}

/**
 * The price of these goods, in cents. Write it as ONE `when (this)` with a branch per node type and
 * no `else`, calling `price` again on what a group holds.
 */
fun Goods.price(): Long =
    TODO("one when over the five node types: leaves compute, groups ask what they hold")

/**
 * A one-line description for the receipt:
 *
 *  - `Item("jam", 300)` is `jam 3.00`; `Item("card", 5)` is `card 0.05`
 *  - `ByWeight("coffee", 250, 2_400)` is `coffee 250 g`
 *  - `Box(a, b)` is `(a + b)`, and an empty Box is `()`
 *  - `PercentOff(x, 10)` is `10% off x`
 *  - `Deal(x, 800)` is `min(x, 8.00)`
 */
fun Goods.describe(): String =
    TODO("one when again; joinToString builds the box form")
