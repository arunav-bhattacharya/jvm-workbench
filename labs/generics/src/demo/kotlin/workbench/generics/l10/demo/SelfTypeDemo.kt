package workbench.generics.l10.demo

// 1. Without a self type: the base setters return the base class, and the chain loses the subclass.
open class PlainBuilder {
    protected var grams = 0
    fun grams(grams: Int): PlainBuilder { this.grams = grams; return this }
}
class PlainGiftBoxBuilder : PlainBuilder() {
    private var ribbon = ""
    fun ribbon(colour: String): PlainGiftBoxBuilder { ribbon = colour; return this }
    fun build() = "gift box, $grams g, $ribbon ribbon"
}

// 2. With a self type: B names "my own subclass", so the base setters return it.
abstract class Builder<B : Builder<B>> {
    protected var grams = 0
    fun grams(grams: Int): B { this.grams = grams; return self() }
    protected abstract fun self(): B
}
class GiftBoxBuilder : Builder<GiftBoxBuilder>() {
    private var ribbon = ""
    fun ribbon(colour: String): GiftBoxBuilder { ribbon = colour; return this }
    override fun self() = this
    fun build() = "gift box, $grams g, $ribbon ribbon"
}

fun main() {
    val lost: PlainBuilder = PlainGiftBoxBuilder().ribbon("red").grams(1_200)   // grams() returns a PlainBuilder
    println("after grams(): static type PlainBuilder, run-time class ${lost::class.simpleName}")
    println(GiftBoxBuilder().grams(1_200).ribbon("red").build())    // the chain keeps GiftBoxBuilder

    // Wrong moves. Uncomment one at a time, predict the error, then run.
    // println(PlainGiftBoxBuilder().grams(1_200).ribbon("red").build())          // 1
    // class Liar : Builder<GiftBoxBuilder>() { override fun self() = GiftBoxBuilder() }   // 2 (compiles: what does it break?)
}
