package workbench.patterns.l10

// The same breakfast box priced with a classic Visitor and with a sealed when, then checked by an inspector.

interface GoodsVisitor<R> {
    fun visitItem(i: Item): R
    fun visitFresh(f: Fresh): R
    fun visitBox(b: Box): R
}

sealed interface Goods { fun <R> accept(v: GoodsVisitor<R>): R }
data class Item(val name: String, val cents: Long) : Goods {
    override fun <R> accept(v: GoodsVisitor<R>) = v.visitItem(this)
}
data class Fresh(val name: String, val cents: Long, val daysLeft: Int) : Goods {
    override fun <R> accept(v: GoodsVisitor<R>) = v.visitFresh(this)
}
data class Box(val contents: List<Goods>) : Goods {
    override fun <R> accept(v: GoodsVisitor<R>) = v.visitBox(this)
}

// operation 1, visitor style: one class per operation, one method per kind of goods
object Price : GoodsVisitor<Long> {
    override fun visitItem(i: Item) = i.cents
    override fun visitFresh(f: Fresh) = if (f.daysLeft == 0) f.cents / 2 else f.cents
    override fun visitBox(b: Box) = b.contents.sumOf { it.accept(this) }
}

// operation 1 again, data style: no accept needed, no visitor interface
private fun price(g: Goods): Long = when (g) {
    is Item -> g.cents
    is Fresh if g.daysLeft == 0 -> g.cents / 2               // last day: half price
    is Fresh -> g.cents
    is Box -> g.contents.sumOf { price(it) }
}

// operation 2, the inspector: just one more function, with a different check for each kind
private fun inspect(g: Goods): List<String> = when (g) {
    is Item -> if (g.cents > 0) emptyList() else listOf("${g.name}: no price label")
    is Fresh -> if (g.daysLeft > 0) emptyList() else listOf("${g.name}: last day")
    is Box -> g.contents.flatMap { inspect(it) }
}

fun main() {
    val breakfast = Box(listOf(Fresh("rye bread", 250, 2), Item("jam", 300),
        Box(listOf(Item("tea", 450), Fresh("milk", 120, 0)))))
    println("breakfast box: ${breakfast.accept(Price)} cents (visitor) = ${price(breakfast)} cents (when)")
    println("inspector found: ${inspect(breakfast)}")
}
